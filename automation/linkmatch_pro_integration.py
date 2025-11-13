#!/usr/bin/env python3

"""
LINKMATCH PRO INTEGRATION MODULE
Full integration with LinkMatch Pro for LinkedIn automation via HubSpot.
Leverages AI insights, bulk exports, and connection management.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

# Configure logging
logger = logging.getLogger("linkmatch_integration")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
	logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
)
logger.addHandler(handler)

# Database setup
engine = create_engine(DB_URL)

# HubSpot API base URL
HUBSPOT_API_BASE = "https://api.hubapi.com"


class LinkedInProfile(BaseModel):
	"""LinkedIn profile data from LinkMatch"""
	linkedin_url: Optional[str]
	headline: Optional[str]
	bio: Optional[str]
	connections: Optional[int]
	posts_count: Optional[int]
	last_activity: Optional[str]
	connection_status: str  # not_connected, pending, connected
	verified_email: Optional[str]
	
	
class LinkMatchAIInsights(BaseModel):
	"""AI-powered insights from LinkMatch Pro"""
	is_decision_maker: bool
	engagement_score: int  # 0-100
	best_time_to_contact: Optional[str]
	communication_style: Optional[str]  # formal, casual, technical
	buying_signals: List[str]
	pain_points_detected: List[str]
	custom_insights: List[str]
	
	
# ============================================================================
# CORE LINKMATCH DATA RETRIEVAL
# ============================================================================
	
async def get_linkedin_profile_from_hubspot(contact_id: str) -> LinkedInProfile:
	"""
	Retrieve LinkedIn profile data synced by LinkMatch
	LinkMatch → HubSpot → Sales Angel
	"""
	url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
	
	headers = {
		"Authorization": f"Bearer {HUBSPOT_API_KEY}",
		"Content-Type": "application/json"
	}
	
	# LinkMatch Pro custom fields in HubSpot
	params = {
		"properties": [
			"linkedin_profile_url",
			"linkedin_headline",
			"linkedin_bio",
			"linkedin_connections_count",
			"linkedin_posts_count",
			"linkedin_last_activity_date",
			"linkmatch_connection_status",
			"linkmatch_verified_email",
			"linkmatch_sync_date"
		]
	}
	
	try:
		async with httpx.AsyncClient(timeout=15.0) as client:
			response = await client.get(url, headers=headers, params=params)
			response.raise_for_status()
			
			props = response.json()["properties"]
			
			profile = LinkedInProfile(
				linkedin_url=props.get("linkedin_profile_url"),
				headline=props.get("linkedin_headline"),
				bio=props.get("linkedin_bio"),
				connections=int(props.get("linkedin_connections_count", 0)) if props.get("linkedin_connections_count") else None,
				posts_count=int(props.get("linkedin_posts_count", 0)) if props.get("linkedin_posts_count") else None,
				last_activity=props.get("linkedin_last_activity_date"),
				connection_status=props.get("linkmatch_connection_status", "not_connected"),
				verified_email=props.get("linkmatch_verified_email")
			)
			
			logger.info(f"Retrieved LinkedIn profile for contact {contact_id}")
			return profile
		
	except httpx.HTTPError as e:
		logger.error(f"HubSpot API error retrieving LinkedIn profile: {str(e)}")
		return LinkedInProfile(connection_status="error")
	except Exception as e:
		logger.error(f"Error retrieving LinkedIn profile: {str(e)}")
		return LinkedInProfile(connection_status="error")
	
	
async def get_linkmatch_ai_insights(contact_id: str) -> LinkMatchAIInsights:
	"""
	Retrieve AI-powered insights from LinkMatch Pro
	Uses custom prompts configured in LinkMatch Pro
	"""
	url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
	
	headers = {
		"Authorization": f"Bearer {HUBSPOT_API_KEY}",
		"Content-Type": "application/json"
	}
	
	# LinkMatch Pro AI fields
	params = {
		"properties": [
			"linkmatch_ai_decision_maker",
			"linkmatch_ai_engagement_score",
			"linkmatch_ai_best_contact_time",
			"linkmatch_ai_communication_style",
			"linkmatch_ai_buying_signals",
			"linkmatch_ai_pain_points",
			"linkmatch_custom_prompt_1",  # Configurable custom prompts
			"linkmatch_custom_prompt_2",
			"linkmatch_custom_prompt_3"
		]
	}
	
	try:
		async with httpx.AsyncClient(timeout=15.0) as client:
			response = await client.get(url, headers=headers, params=params)
			response.raise_for_status()
			
			props = response.json()["properties"]
			
			# Parse buying signals and pain points (stored as comma-separated)
			buying_signals = props.get("linkmatch_ai_buying_signals", "").split(",") if props.get("linkmatch_ai_buying_signals") else []
			pain_points = props.get("linkmatch_ai_pain_points", "").split(",") if props.get("linkmatch_ai_pain_points") else []
			
			# Custom insights
			custom_insights = [
				props.get("linkmatch_custom_prompt_1"),
				props.get("linkmatch_custom_prompt_2"),
				props.get("linkmatch_custom_prompt_3")
			]
			custom_insights = [i for i in custom_insights if i]  # Filter None values
			
			insights = LinkMatchAIInsights(
				is_decision_maker=props.get("linkmatch_ai_decision_maker") == "true",
				engagement_score=int(props.get("linkmatch_ai_engagement_score", 0)),
				best_time_to_contact=props.get("linkmatch_ai_best_contact_time"),
				communication_style=props.get("linkmatch_ai_communication_style"),
				buying_signals=[s.strip() for s in buying_signals if s.strip()],
				pain_points_detected=[p.strip() for p in pain_points if p.strip()],
				custom_insights=custom_insights
			)
			
			logger.info(f"Retrieved AI insights for contact {contact_id}")
			return insights
		
	except Exception as e:
		logger.error(f"Error retrieving AI insights: {str(e)}")
		return LinkMatchAIInsights(
			is_decision_maker=False,
			engagement_score=0,
			buying_signals=[],
			pain_points_detected=[],
			custom_insights=[]
		)
	
	
# ============================================================================
# LINKEDIN CONNECTION MANAGEMENT
# ============================================================================
	
async def check_linkedin_connection_status(contact_id: str) -> str:
	"""
	Check current LinkedIn connection status
	Returns: not_connected, pending, connected, error
	"""
	profile = await get_linkedin_profile_from_hubspot(contact_id)
	return profile.connection_status


async def request_linkedin_connection(contact_id: str, message: Optional[str] = None) -> bool:
	"""
	Queue LinkedIn connection request via LinkMatch
	Method: Update HubSpot field that LinkMatch monitors
	"""
	# First check if already connected
	status = await check_linkedin_connection_status(contact_id)
	
	if status == "connected":
		logger.info(f"Contact {contact_id} already connected - skipping")
		return True
	
	if status == "pending":
		logger.info(f"Connection request already pending for {contact_id}")
		return True
	
	url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
	
	headers = {
		"Authorization": f"Bearer {HUBSPOT_API_KEY}",
		"Content-Type": "application/json"
	}
	
	# Update HubSpot fields to trigger LinkMatch action
	payload = {
		"properties": {
			"linkmatch_action": "send_connection_request",
			"linkmatch_action_timestamp": datetime.now().isoformat(),
			"linkmatch_connection_message": message or "I'd like to connect!",
			"linkmatch_action_status": "queued"
		}
	}
	
	try:
		async with httpx.AsyncClient(timeout=15.0) as client:
			response = await client.patch(url, headers=headers, json=payload)
			response.raise_for_status()
			
			logger.info(f"LinkedIn connection request queued for contact {contact_id}")
			
			# Log to database
			with engine.begin() as conn:
				conn.execute(
					text("""
						INSERT INTO linkedin_actions 
						(contact_id, action_type, status, created_at)
						VALUES (:cid, 'connection_request', 'queued', NOW())
					"""),
					{"cid": contact_id}
				)
				
			return True
		
	except Exception as e:
		logger.error(f"Error queueing connection request: {str(e)}")
		return False
	
	
async def send_linkedin_message(contact_id: str, message: str) -> bool:
	"""
	Send LinkedIn message via LinkMatch
	Requires existing connection
	"""
	# Check connection status
	status = await check_linkedin_connection_status(contact_id)
	
	if status != "connected":
		logger.warning(f"Cannot send message - not connected to {contact_id}")
		return False
	
	url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
	
	headers = {
		"Authorization": f"Bearer {HUBSPOT_API_KEY}",
		"Content-Type": "application/json"
	}
	
	payload = {
		"properties": {
			"linkmatch_action": "send_message",
			"linkmatch_action_timestamp": datetime.now().isoformat(),
			"linkmatch_message_content": message,
			"linkmatch_action_status": "queued"
		}
	}
	
	try:
		async with httpx.AsyncClient(timeout=15.0) as client:
			response = await client.patch(url, headers=headers, json=payload)
			response.raise_for_status()
			
			logger.info(f"LinkedIn message queued for contact {contact_id}")
			
			# Log to database
			with engine.begin() as conn:
				conn.execute(
					text("""
						INSERT INTO linkedin_actions 
						(contact_id, action_type, message, status, created_at)
						VALUES (:cid, 'message_sent', :msg, 'queued', NOW())
					"""),
					{"cid": contact_id, "msg": message[:500]}  # Truncate if needed
				)
				
			return True
		
	except Exception as e:
		logger.error(f"Error queueing LinkedIn message: {str(e)}")
		return False
	
	
# ============================================================================
# BULK OPERATIONS
# ============================================================================
	
async def bulk_import_linkedin_contacts(search_url: Optional[str] = None, limit: int = 500):
	"""
	Import contacts from LinkMatch bulk export
	LinkMatch Pro allows exporting up to 500 profiles at once
	
	Workflow:
	1. User performs LinkedIn search or Sales Navigator search
	2. LinkMatch Pro exports to HubSpot (max 500)
	3. This function detects new imports and enriches them
	"""
	logger.info("Starting bulk import from LinkMatch")
	
	url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
	
	headers = {
		"Authorization": f"Bearer {HUBSPOT_API_KEY}",
		"Content-Type": "application/json"
	}
	
	# Query for recently added contacts from LinkMatch
	payload = {
		"filterGroups": [{
			"filters": [
				{
					"propertyName": "hs_analytics_source",
					"operator": "CONTAINS_TOKEN",
					"value": "linkmatch"
				},
				{
					"propertyName": "createdate",
					"operator": "GTE",
					"value": (datetime.now() - timedelta(hours=1)).timestamp() * 1000  # Last hour
				}
			]
		}],
		"properties": ["id", "email", "firstname", "lastname", "company"],
		"limit": limit
	}
	
	try:
		async with httpx.AsyncClient(timeout=30.0) as client:
			response = await client.post(url, headers=headers, json=payload)
			response.raise_for_status()
			
			results = response.json()["results"]
			contact_ids = [r["id"] for r in results]
			
			logger.info(f"Found {len(contact_ids)} new contacts from LinkMatch")
			
			# Import to Sales Angel database
			imported = 0
			for contact_id in contact_ids:
				try:
					# Check if already exists
					with engine.connect() as conn:
						exists = conn.execute(
							text("SELECT id FROM contacts WHERE crm_id = :cid"),
							{"cid": contact_id}
						).fetchone()
						
					if not exists:
						# Get full contact data
						contact_data = await get_full_contact_data(contact_id)
						
						# Insert to database
						with engine.begin() as conn:
							conn.execute(
								text("""
									INSERT INTO contacts 
									(crm_id, name, email, company, phone, linkedin_url, source, created_at)
									VALUES (:cid, :name, :email, :company, :phone, :linkedin, 'linkmatch', NOW())
								"""),
								{
									"cid": contact_id,
									"name": contact_data.get("name"),
									"email": contact_data.get("email"),
									"company": contact_data.get("company"),
									"phone": contact_data.get("phone"),
									"linkedin": contact_data.get("linkedin_url")
								}
							)
							
						imported += 1
						logger.info(f"Imported contact {contact_id}")
						
				except Exception as e:
					logger.error(f"Error importing contact {contact_id}: {str(e)}")
					continue
				
			return {
				"status": "success",
				"total_found": len(contact_ids),
				"imported": imported,
				"message": f"Imported {imported} new contacts from LinkMatch"
			}
		
	except Exception as e:
		logger.error(f"Error in bulk import: {str(e)}")
		return {"status": "error", "error": str(e)}
	
	
async def get_full_contact_data(contact_id: str) -> Dict:
	"""Retrieve complete contact data from HubSpot"""
	url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
	headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}"}
	
	try:
		async with httpx.AsyncClient() as client:
			response = await client.get(url, headers=headers)
			props = response.json()["properties"]
			
			return {
				"name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
				"email": props.get("email"),
				"company": props.get("company"),
				"phone": props.get("phone"),
				"linkedin_url": props.get("linkedin_profile_url")
			}
	except:
		return {}
	
	
# ============================================================================
# AI-ENHANCED ENRICHMENT
# ============================================================================
	
async def enrich_with_linkmatch_ai(contact_id: str) -> Dict:
	"""
	Enhance Sales Angel enrichment with LinkMatch Pro AI insights
	Combines Profile Builder (Module 2) with LinkMatch AI
	"""
	# Get LinkMatch data
	linkedin_profile = await get_linkedin_profile_from_hubspot(contact_id)
	ai_insights = await get_linkmatch_ai_insights(contact_id)
	
	# Get existing Sales Angel profile
	try:
		with engine.connect() as conn:
			result = conn.execute(
				text("SELECT profile_json FROM profiles WHERE contact_id = :cid"),
				{"cid": contact_id}
			).fetchone()
			
			if result:
				existing_profile = result[0]
			else:
				existing_profile = {}
	except:
		existing_profile = {}
		
	# Merge data
	enhanced_profile = existing_profile.copy()
	
	# Add LinkMatch AI insights to sales_talking_points
	if "sales_talking_points" not in enhanced_profile:
		enhanced_profile["sales_talking_points"] = {}
		
	enhanced_profile["sales_talking_points"]["linkmatch_buying_signals"] = ai_insights.buying_signals
	enhanced_profile["sales_talking_points"]["linkmatch_pain_points"] = ai_insights.pain_points_detected
	enhanced_profile["sales_talking_points"]["linkmatch_engagement_score"] = ai_insights.engagement_score
	enhanced_profile["sales_talking_points"]["linkmatch_best_time"] = ai_insights.best_time_to_contact
	
	# Add to personality section
	if "mbti_interpretation" not in enhanced_profile:
		enhanced_profile["mbti_interpretation"] = {}
		
	enhanced_profile["mbti_interpretation"]["linkmatch_communication_style"] = ai_insights.communication_style
	
	# Add decision maker flag
	enhanced_profile["linkmatch_is_decision_maker"] = ai_insights.is_decision_maker
	
	# Add custom AI insights
	enhanced_profile["linkmatch_custom_insights"] = ai_insights.custom_insights
	
	# Update database
	try:
		with engine.begin() as conn:
			conn.execute(
				text("""
					UPDATE profiles 
					SET profile_json = :profile, 
						linkmatch_enriched = TRUE,
						linkmatch_enriched_at = NOW()
					WHERE contact_id = :cid
				"""),
				{"profile": json.dumps(enhanced_profile), "cid": contact_id}
			)
	except Exception as e:
		logger.error(f"Error updating profile with LinkMatch data: {str(e)}")
		
	logger.info(f"Enhanced profile with LinkMatch AI for contact {contact_id}")
	return enhanced_profile


# ============================================================================
# AUTOMATED WORKFLOWS
# ============================================================================

async def auto_connect_high_score_leads():
	"""
	Automatically send LinkedIn connection requests to high-scoring leads
	Runs daily via cron
	"""
	logger.info("Starting auto-connect for high-score leads")
	
	# Get leads with score >= 70 who aren't connected
	try:
		with engine.connect() as conn:
			results = conn.execute(
				text("""
					SELECT c.id, c.crm_id 
					FROM contacts c
					INNER JOIN lead_scores ls ON c.id = ls.contact_id
					WHERE ls.total_score >= 70
					AND c.linkedin_url IS NOT NULL
					AND NOT EXISTS (
						SELECT 1 FROM linkedin_actions la 
						WHERE la.contact_id = c.id 
						AND la.action_type = 'connection_request'
						AND la.created_at >= NOW() - INTERVAL '30 days'
					)
					LIMIT 50
				""")
			).fetchall()
			
		connected = 0
		for row in results:
			contact_id = str(row[0])
			
			# Check LinkMatch status
			status = await check_linkedin_connection_status(contact_id)
			
			if status == "not_connected":
				# Generate personalized message using AI insights
				insights = await get_linkmatch_ai_insights(contact_id)
				
				message = "I'd like to connect!"
				if insights.custom_insights:
					message = insights.custom_insights[0][:300]  # Use first custom insight
					
				success = await request_linkedin_connection(contact_id, message)
				if success:
					connected += 1
					
		logger.info(f"Auto-connected {connected} high-score leads")
		return {"status": "success", "connected": connected}
	
	except Exception as e:
		logger.error(f"Error in auto-connect workflow: {str(e)}")
		return {"status": "error", "error": str(e)}
	
	
# ============================================================================
# FASTAPI ENDPOINTS
# ============================================================================
	
from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncio

router = APIRouter()


@router.get("/api/linkmatch/profile/{contact_id}")
async def linkmatch_profile_endpoint(contact_id: str):
	"""Get LinkedIn profile data from LinkMatch"""
	try:
		profile = await get_linkedin_profile_from_hubspot(contact_id)
		return profile.dict()
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
		
		
@router.get("/api/linkmatch/insights/{contact_id}")
async def linkmatch_insights_endpoint(contact_id: str):
	"""Get AI insights from LinkMatch Pro"""
	try:
		insights = await get_linkmatch_ai_insights(contact_id)
		return insights.dict()
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
		
		
@router.post("/api/linkmatch/connect/{contact_id}")
async def linkmatch_connect_endpoint(contact_id: str, message: Optional[str] = None):
	"""Request LinkedIn connection via LinkMatch"""
	try:
		success = await request_linkedin_connection(contact_id, message)
		return {"status": "success" if success else "failed", "contact_id": contact_id}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
		
		
@router.post("/api/linkmatch/message/{contact_id}")
async def linkmatch_message_endpoint(contact_id: str, message: str):
	"""Send LinkedIn message via LinkMatch"""
	try:
		success = await send_linkedin_message(contact_id, message)
		return {"status": "success" if success else "failed", "contact_id": contact_id}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
		
		
@router.post("/api/linkmatch/bulk-import")
async def linkmatch_bulk_import_endpoint(background_tasks: BackgroundTasks, limit: int = 500):
	"""Import contacts from LinkMatch bulk export"""
	background_tasks.add_task(bulk_import_linkedin_contacts, limit=limit)
	return {
		"status": "started",
		"message": "Bulk import initiated in background"
	}
	

@router.post("/api/linkmatch/enrich/{contact_id}")
async def linkmatch_enrich_endpoint(contact_id: str):
	"""Enhance profile with LinkMatch AI insights"""
	try:
		profile = await enrich_with_linkmatch_ai(contact_id)
		return {"status": "success", "profile": profile}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
		
		
@router.post("/api/linkmatch/auto-connect")
async def linkmatch_auto_connect_endpoint(background_tasks: BackgroundTasks):
	"""Auto-connect to high-score leads (cron job)"""
	background_tasks.add_task(auto_connect_high_score_leads)
	return {
		"status": "started",
		"message": "Auto-connect workflow initiated"
	}
	

@router.get("/api/linkmatch/status/{contact_id}")
async def linkmatch_status_endpoint(contact_id: str):
	"""Get LinkedIn connection status"""
	try:
		status = await check_linkedin_connection_status(contact_id)
		return {"contact_id": contact_id, "status": status}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
		