from fastapi import APIRouter, Query
from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from globals import logger_manager, config, main_logger
from core.database.db_manager import get_database
from core.database.base import CompanyProfile, UserProfile
from typing import Optional
import asyncio
import json

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])

@router.get("/{company_id}/{candidate_id}")
async def get_latest_evaluation(
    company_id: str, 
    candidate_id: str, 
    job_title: Optional[str] = Query(None, description="Filter by job title")
):
    global main_logger
    log_msg = f"Getting latest evaluation for candidate: {candidate_id} from company: {company_id}"
    if job_title:
        log_msg += f" for job title: {job_title}"
    main_logger.info(log_msg)
    
    try:
        database = await get_database(main_logger)
        
        # First, verify the company exists and get company details
        company_data:CompanyProfile|None = await database.get_company_by_id(company_id)
        if company_data is None:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get user data and verify they belong to this company
        firebase_user_id = await database.get_user_id_by_email(candidate_id)
        if firebase_user_id is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify user belongs to the specified company
        user_data:UserProfile|None = await database.get_user_by_id(firebase_user_id)
        if user_data is None or user_data.company_name != company_data.name or user_data.job_title != job_title:
            raise HTTPException(status_code=403, detail="User does not belong to this company")
        
        # Get the evaluation data
        # If job_title is provided, we should filter sessions by job title
        # For now, get the latest session, but in a full implementation,
        # we would filter sessions based on the job title from session metadata
        latest_session = await database.get_most_recent_session_id_by_user_id(firebase_user_id)
        data = await database.get_final_visualisation_report_from_database(firebase_user_id, latest_session)
        
        if data is None:
            raise HTTPException(status_code=404, detail="No evaluation data found for this user")
        
        evaluation_report = data.get("visualisation_report", None)
            
        return evaluation_report
        
    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error getting evaluation for candidate {candidate_id} from company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary/{company_id}")
async def get_latest_evaluation_by_company(
    company_id: str,
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    min_score: Optional[float] = Query(None, description="Filter by minimum score"),
    max_score: Optional[float] = Query(None, description="Filter by maximum score"),
    job_title: Optional[str] = Query(None, description="Filter by job title"),
    status: Optional[str] = Query(None, description="Filter by status (completed, evaluated, in_progress)")
):
    async def generate():
        global main_logger
        # Build filter log message
        filters = []
        if start_date: filters.append(f"start_date={start_date}")
        if end_date: filters.append(f"end_date={end_date}")
        if min_score is not None: filters.append(f"min_score={min_score}")
        if max_score is not None: filters.append(f"max_score={max_score}")
        if job_title: filters.append(f"job_title={job_title}")
        if status: filters.append(f"status={status}")
        
        filter_str = f" with filters: {', '.join(filters)}" if filters else ""
        main_logger.info(f"Getting latest evaluation for company ID: {company_id}{filter_str}")
        
        try:
            database = await get_database(main_logger)
            
            # First, verify the company exists and get company details
            company_data = await database.get_company_by_id(company_id)
            if company_data is None:
                yield json.dumps({"error": "Company not found"})
                return
            
            # Get all users that belong to this company
            users = await database.get_all_users_data()
            user_company_name_list = [users[i] for i in range(len(users)) if users[i].company_name == company_data.name]
            
            evaluation_data_list = []
            for user in user_company_name_list:
                firebase_id = user.user_id
                if firebase_id is None:
                    continue
                    
                latest_session = await database.get_most_recent_session_id_by_user_id(firebase_id)
                data = await database.get_final_visualisation_report_from_database(firebase_id, latest_session)
                
                if data is not None and data.get("visualisation_report", None) is not None:
                    evaluation_report = data.get("visualisation_report")
                    
                    # Apply filters
                    should_include = True
                    
                    # Filter by job title
                    if job_title and should_include:
                        try:
                            report_position = evaluation_report.get('position') or evaluation_report.get('job_title')
                            if report_position:
                                if job_title.lower() not in report_position.lower():
                                    should_include = False
                            else:
                                should_include = False
                        except (KeyError, AttributeError):
                            should_include = False
                    
                    # Filter by score range
                    if (min_score is not None or max_score is not None) and should_include:
                        try:
                            overall_score = evaluation_report.get('overall_score')
                            if overall_score is not None:
                                if min_score is not None and overall_score < min_score:
                                    should_include = False
                                if max_score is not None and overall_score > max_score:
                                    should_include = False
                            else:
                                should_include = False
                        except (KeyError, AttributeError):
                            should_include = False
                    
                    # Filter by date range (if interview_date exists in evaluation)
                    if (start_date or end_date) and should_include:
                        try:
                            interview_date = evaluation_report.get('interview_date')
                            if interview_date:
                                from datetime import datetime
                                eval_date = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
                                
                                if start_date:
                                    start_dt = datetime.fromisoformat(start_date + 'T00:00:00')
                                    if eval_date < start_dt:
                                        should_include = False
                                
                                if end_date and should_include:
                                    end_dt = datetime.fromisoformat(end_date + 'T23:59:59')
                                    if eval_date > end_dt:
                                        should_include = False
                            else:
                                # If no date info, exclude when date filter is applied
                                should_include = False
                        except (ValueError, KeyError, AttributeError):
                            should_include = False
                    
                    # Filter by status (this would need to be determined based on evaluation completeness)
                    if status and should_include:
                        try:
                            # Assume completed evaluations have overall_score, otherwise pending
                            eval_status = 'completed' if evaluation_report.get('overall_score') else 'in_progress'
                            if status != eval_status:
                                should_include = False
                        except (KeyError, AttributeError):
                            should_include = False
                    
                    if should_include:
                        evaluation_data_list.append(evaluation_report)
            
            yield json.dumps(evaluation_data_list)
            
        except Exception as e:
            main_logger.error(f"Error getting evaluations for company {company_id}: {e}")
            yield json.dumps({"error": "Internal server error"})

    return StreamingResponse(generate(), media_type="application/json")