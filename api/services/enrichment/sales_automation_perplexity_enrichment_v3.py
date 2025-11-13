#!/usr/bin/env python3
"""
Perplexity Enrichment Module v3
Structured JSON-based enrichment with robust error handling
"""

import sys
import os
import json
import re
import logging
import requests
from datetime import datetime
from typing import Dict, Tuple, Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/enrichment_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global stats tracker
enrichment_stats = {
    'total': 0,
    'success': 0,
    'partial': 0,
    'failed': 0,
    'score_errors': 0,
    'insights_errors': 0,
    'api_errors': 0
}


def log_enrichment_error(contact_email: str, error_type: str, details: str, raw_response: Optional[str] = None):
    """
    Log enrichment failures for later review and debugging

    Args:
        contact_email: Contact email address
        error_type: Type of error (score_parse, insights_parse, api_error)
        details: Error description
        raw_response: Raw API response for debugging
    """
    logger.error(f"ENRICHMENT_ERROR | {contact_email} | {error_type} | {details}")

    # Write structured log for analysis
    error_record = {
        'timestamp': datetime.now().isoformat(),
        'email': contact_email,
        'error_type': error_type,
        'details': str(details),
        'raw_response': raw_response[:500] if raw_response else None  # Truncate for readability
    }

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    with open('data/enrichment_failures.json', 'a') as f:
        f.write(json.dumps(error_record) + '\n')

    # Update stats
    enrichment_stats[f'{error_type}s'] = enrichment_stats.get(f'{error_type}s', 0) + 1


def parse_perplexity_json(response_text: str, expected_keys: list) -> Tuple[Optional[Dict], str]:
    """
    Multi-strategy JSON parser with comprehensive fallbacks

    Args:
        response_text: Raw response from Perplexity API
        expected_keys: List of required keys in JSON response

    Returns:
        Tuple of (parsed_data_dict, status_string)
        Status: 'complete', 'partial', or raw_text (if failed)
    """

    # Strategy 1: Direct JSON parse
    try:
        data = json.loads(response_text)
        if all(k in data for k in expected_keys):
            logger.debug(f"Strategy 1 success: Direct JSON parse")
            return data, 'complete'
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract JSON from markdown code blocks
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    for match in matches:
        try:
            data = json.loads(match)
            if all(k in data for k in expected_keys):
                logger.debug(f"Strategy 2 success: Markdown code block extraction")
                return data, 'complete'
        except json.JSONDecodeError:
            continue

    # Strategy 3: Find any JSON object in text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    for match in matches:
        try:
            data = json.loads(match)
            if all(k in data for k in expected_keys):
                logger.debug(f"Strategy 3 success: JSON object extraction")
                return data, 'complete'
        except json.JSONDecodeError:
            continue

    # Strategy 4: Regex fallback for score extraction (partial recovery)
    if 'score' in expected_keys:
        score_patterns = [
            r'"score"\s*:\s*(\d{1,3})',
            r"'score'\s*:\s*(\d{1,3})",
            r'score:\s*(\d{1,3})',
            r'Score:\s*(\d{1,3})',
            r'score of (\d{1,3})',
            r'rated (\d{1,3})'
        ]
        for pattern in score_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    logger.warning(f"Strategy 4: Partial recovery - extracted score {score}")
                    return {'score': score, 'reasoning': 'Partial extraction', 'confidence': 'low'}, 'partial'

    # All strategies failed
    logger.error(f"All parsing strategies failed. Response: {response_text[:200]}...")
    return None, response_text


def get_structured_score(props: Dict[str, Any], api_key: str, model: str = "sonar-pro") -> Tuple[Optional[Dict], str]:
    """
    Get AI prospect score with structured JSON response

    Args:
        props: HubSpot contact properties
        api_key: Perplexity API key
        model: Perplexity model to use

    Returns:
        Tuple of (score_data_dict, status_string)
        score_data_dict contains: score, reasoning, confidence
    """

    name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
    company = props.get('company', 'Unknown')
    title = props.get('jobtitle', 'Unknown')
    industry = props.get('industry', 'Unknown')
    engagement = props.get('engagement_score', 'N/A')
    status = props.get('hs_lead_status', 'Unknown')

    prompt = f"""You are a B2B sales intelligence analyst. Analyze this prospect and return ONLY valid JSON with this exact structure:

{{
  "score": <integer 0-100>,
  "reasoning": "<2-3 sentence explanation of the score>",
  "confidence": "<high|medium|low>"
}}

PROSPECT DETAILS:
- Name: {name}
- Title: {title}
- Company: {company}
- Industry: {industry}
- Engagement Score: {engagement}
- Lead Status: {status}

SCORING CRITERIA:
- Decision-making authority (title/role)
- Company size and growth trajectory
- Industry alignment with our offering
- Engagement signals (if available)
- Likelihood to close a high-value deal

The score must be an integer between 0-100. Provide reasoning that justifies your score. Confidence should reflect certainty of your assessment based on available data.

Return ONLY the JSON object, no additional text."""

    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,  # Lower temperature for more consistent outputs
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )

        if not response.ok:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            enrichment_stats['api_errors'] += 1
            return None, 'api_error'

        result = response.json()
        content = result['choices'][0]['message']['content']

        # Parse JSON response
        score_data, status = parse_perplexity_json(content, ['score', 'reasoning', 'confidence'])

        if score_data:
            # Validate score range
            if not (0 <= score_data.get('score', -1) <= 100):
                logger.warning(f"Score out of range: {score_data.get('score')}")
                score_data['score'] = max(0, min(100, score_data.get('score', 50)))

            logger.info(f"Score extraction success: {score_data.get('score')} ({status})")
            return score_data, status
        else:
            logger.error(f"Score parsing failed. Raw: {content[:200]}")
            enrichment_stats['score_errors'] += 1
            return None, 'parse_error'

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        enrichment_stats['api_errors'] += 1
        return None, 'api_error'
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return None, 'error'


def get_structured_insights(props: Dict[str, Any], api_key: str, model: str = "sonar-pro") -> Tuple[Optional[Dict], str]:
    """
    Get structured prospect insights with detailed breakdown

    Args:
        props: HubSpot contact properties
        api_key: Perplexity API key
        model: Perplexity model to use

    Returns:
        Tuple of (insights_data_dict, status_string)
        insights_data_dict contains: background, company_overview, pain_points,
        outreach_approach, talking_points, recent_activity, decision_authority
    """

    name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
    company = props.get('company', 'Unknown')
    linkedin = props.get('hs_linkedin_account', '')
    title = props.get('jobtitle', 'Unknown')

    prompt = f"""Research {name} ({title}) at {company}. Return ONLY valid JSON with this exact structure:

{{
  "background": "<professional background, career trajectory, 2-3 sentences>",
  "company_overview": "<company positioning, market, growth signals, 2-3 sentences>",
  "pain_points": ["<pain point 1>", "<pain point 2>", "<pain point 3>"],
  "outreach_approach": "<recommended contact strategy based on role/company, 2-3 sentences>",
  "talking_points": ["<discussion topic 1>", "<discussion topic 2>", "<discussion topic 3>"],
  "recent_activity": "<latest news, funding, expansion, LinkedIn activity, 2-3 sentences>",
  "decision_authority": "<High|Medium|Low>"
}}

RESEARCH FOCUS:
- Professional background and current role responsibilities
- Company market position, growth trajectory, recent news
- Likely pain points based on industry/role
- Decision-making authority and buying power
- Best approach for initial outreach
- Key topics that would resonate

LinkedIn: {linkedin}

Return ONLY the JSON object with all fields populated. If information is limited, make reasonable inferences based on title and company."""

    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1500
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
            timeout=45
        )

        if not response.ok:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            enrichment_stats['api_errors'] += 1
            return None, 'api_error'

        result = response.json()
        content = result['choices'][0]['message']['content']

        # Parse JSON response
        expected_keys = ['background', 'company_overview', 'pain_points', 'outreach_approach', 
                        'talking_points', 'recent_activity', 'decision_authority']
        insights_data, status = parse_perplexity_json(content, expected_keys)

        if insights_data:
            # Ensure arrays are actual lists
            if isinstance(insights_data.get('pain_points'), str):
                insights_data['pain_points'] = [insights_data['pain_points']]
            if isinstance(insights_data.get('talking_points'), str):
                insights_data['talking_points'] = [insights_data['talking_points']]

            logger.info(f"Insights extraction success ({status})")
            return insights_data, status
        else:
            logger.error(f"Insights parsing failed. Raw: {content[:200]}")
            enrichment_stats['insights_errors'] += 1
            return None, 'parse_error'

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        enrichment_stats['api_errors'] += 1
        return None, 'api_error'
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return None, 'error'


def get_enrichment_stats() -> Dict:
    """Return current enrichment statistics"""
    return enrichment_stats.copy()


def reset_enrichment_stats():
    """Reset enrichment statistics"""
    global enrichment_stats
    enrichment_stats = {
        'total': 0,
        'success': 0,
        'partial': 0,
        'failed': 0,
        'score_errors': 0,
        'insights_errors': 0,
        'api_errors': 0
    }


def print_enrichment_summary():
    """Print formatted summary of enrichment run"""
    stats = get_enrichment_stats()
    success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0

    print("\n" + "="*60)
    print("ENRICHMENT SUMMARY")
    print("="*60)
    print(f"Total Contacts:        {stats['total']}")
    print(f"Successful:            {stats['success']} ({success_rate:.1f}%)")
    print(f"Partial:               {stats['partial']}")
    print(f"Failed:                {stats['failed']}")
    print(f"Score Parse Errors:    {stats['score_errors']}")
    print(f"Insights Parse Errors: {stats['insights_errors']}")
    print(f"API Errors:            {stats['api_errors']}")
    print("="*60)
    print(f"\nError log: data/enrichment_errors.log")
    print(f"Failed records: data/enrichment_failures.json")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test functions
    print("Perplexity Enrichment Module v3")
    print("Import this module to use structured enrichment functions")
# This function ensures all insights are strings, not lists
def normalize_insights(insights_dict):
    """Convert any list values to comma-separated strings"""
    normalized = {}
    for key, value in insights_dict.items():
        if isinstance(value, list):
            normalized[key] = ', '.join(str(v) for v in value if v)
        elif value is None:
            normalized[key] = ''
        else:
            normalized[key] = str(value) if not isinstance(value, str) else value
    return normalized
