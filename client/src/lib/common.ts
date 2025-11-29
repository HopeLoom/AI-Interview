
// This file contains common interfaces and enums used in the application

export enum TOPICS {

    INTRODUCTION_AND_ROLE_FIT = "Introduction & Role Fit",
    EXPECTATIONS_AND_FINAL_QUESTIONS = "Expectations & Final Questions",
    TEAM_INTRODUCTION_AND_INTERVIEW_FORMAT = "Team Introductions and Interview Format",
    PROBLEM_INTRODUCTION_AND_CLARIFICATION_SOLVING = "Problem Introduction, Clarification and Problem Solving Task",
    DEEP_DIVE_AND_QA = "Deep Dive & Q&A"
}

export enum SUBTOPICS {
    INTRODUCTION_AND_INTERVIEW_OVERVIEW = "Introductions & Interview Overview",
    JOB_ROLE_FIT = "Job & Role Fit",
    MOTIVATION_AND_CAREER_GOALS = "Motivation & Career Goals",
    WORK_AND_GROWTH_EXPECTATIONS = "Work & Growth Expectations",
    FINAL_QUESTIONS = "Final Questions",
    PANEL_MEMBER_INTRODUCTION = "Panel Member Introductions",
    INTERVIEW_ROUND_OVERVIEW = "Interview Round Overview",
    TECHNICAL_PROBLEM_OVERVIEW = "Technical Problem Overview and Expectation Confirmation",
    PROBLEM_SOLVING_TASK = "Problem Solving Task",
    TASK_SPECIFIC_DISCUSSION = "Task-Specific Discussion",
    CONCEPTUAL_KNOWLEDGE_CHECK = "Conceptual Knowledge Check",
    BROADER_EXPERTISE_ASSESSMENT = "Broader Expertise Assessment"
}

// Enum for different types of WebSocket messages that are sent to the server from the client
export enum WebSocketMessageTypeToServer {
    USER_LOGIN = "USER_LOGIN", 
    INSTRUCTION = "INSTRUCTION",
    INTERVIEW_START = "INTERVIEW_START",
    INTERVIEW_DATA = "INTERVIEW_DATA",
    DONE_PROBLEM_SOLVING = "DONE_PROBLEM_SOLVING",
    ACTIVITY_INFO = "ACTIVITY_INFO",
    INTERVIEW_END = "INTERVIEW_END",
    AUDIO_PLAYBACK_COMPLETED = "AUDIO_PLAYBACK_COMPLETED",
    USER_LOGOUT = "USER_LOGOUT",
    AUDIO_RAW_DATA = "AUDIO_RAW_DATA",
    START_AUDIO_STREAMING = "START_AUDIO_STREAMING",
    EVALUATION_DATA = "EVALUATION_DATA",
    LOAD_CONFIGURATION = "LOAD_CONFIGURATION"
}

// Enum for different types of WebSocket messages that are sent to the client from the server
export enum WebSocketMessageTypeFromServer {
    INTERVIEW_DETAILS = "INTERVIEW_DETAILS",
    USER_PROFILE = "USER_PROFILE",
    INSTRUCTION = "INSTRUCTION",
    INTERVIEW_START = "INTERVIEW_START",
    NEXT_SPEAKER_INFO = "NEXT_SPEAKER_INFO",
    INTERVIEW_DATA = "INTERVIEW_DATA",
    ACTIVITY_INFO = "ACTIVITY_INFO",
    INTERVIEW_END = "INTERVIEW_END",
    AUDIO_SPEECH_TO_TEXT = "AUDIO_SPEECH_TO_TEXT",
    AUDIO_CHUNKS = "AUDIO_CHUNKS",
    AUDIO_STREAMING_COMPLETED = "AUDIO_STREAMING_COMPLETED",
    EVALUATION_DATA = "EVALUATION_DATA",
    ERROR = "ERROR_DATA",
    CONNECTION = "CONNECTION"
}

export interface WebSocketMessageToServer {
    type: WebSocketMessageTypeToServer;
    data: any;
    id: string;
}

export interface SpeechDataToServer {
    raw_audio_data:string;
}

// user login data that is sent to the server
export interface UserLoginDataToServer {
    name: string;
    email: string;
    id: string;
}

// user logout data that is sent to the server
export interface UserLogoutDataToServer {
    id: string;
}

export interface EvaluationDataToServer {
    message:string;
}

// instruction data that is sent to the server
export interface InstructionDataToServer {
    message: string;
}

export interface TextToSpeechDataMessageToServer {
    text:string;
    voice_name:string;
}

export interface TextToSpeechDataMessageFromServer {
    audio_data:string;
}

export interface TextToSpeechStreamingCompletedDataFromServer {
    message:string
}

// interview start data that is sent to the server
export interface InterviewStartDataToServer {
    message: string;
}

export interface InterviewMessageToServer {
    speaker:string,
    message:string,
    activity_data:string
}

export interface InterviewEndDataToServer {
    message: string;
}

export interface AudioPlaybackCompletedDataToServer {
    isAudioPlaybackCompleted: boolean;
}

export interface ActivityInfoDataToServer {
    message: string;
}

export interface LoadConfigurationDataToServer {
    configuration_id: string;
}

export enum SpeakerStatus {
    THINKING = "THINKING",
    SPEAKING = "SPEAKING",
    LISTENING = "LISTENING"
}

export interface WebSocketMessageFromServer { 
    type: WebSocketMessageTypeFromServer;
    data: any;
    id: string;
}

export interface PanelData { 
    id: string;
    name: string;
    avatar?: string;
    isAI: boolean;
    isActive: boolean;
    intro:string;
    interview_round_part_of: InterviewRound;
    connectionStatus: 'connected';
}

export interface ConvertedSpeechFromServer {
    text:string
    speaker_name:string
}

// instruction data that is received from the server
export interface InstructionDataFromServer {
    introduction: string;
    panelists: PanelData[];
    role: string;
    company: string;
    interview_type: string;
}

export interface ActivityInfoFromServer {
    scenario: string;
    data_available: string;
    task_for_the_candidate:string;
    raw_data:string;
    starter_code:string;
}

export enum InterviewRound { 
    ROUND_ONE = "HR_ROUND",
    ROUND_TWO = "TECHNICAL_ROUND",
    ROUND_THREE = "BEHAVIORAL_ROUND"
}

// interview start data that is received from the server
export interface InterviewStartDataFromServer {
    round: InterviewRound;
    participants: PanelData[];
    voice_name: string;
    message: string;
}

// interview data that is received from the server
export interface InterviewMessageFromServer {
    speaker: string;
    text_message: string;
    voice_name: string;
    interview_round: InterviewRound;
    is_user_input_required: boolean;
    current_topic:string;
    current_subtopic:string;
}

export interface MasterChatMessage {
    speaker: string;
    content: string;
}

export interface NextSpeakerInfoFromServer {
    speaker:string;
    is_user_input_required: boolean;
}

// interview end data that is received from the server
export interface InterviewEndDataFromServer {
    message: string;
    voice_name: string;
}

export interface CurrentOccupation {
    occupation: string;
    duration_years: number;
}

export interface Education {
    degree:string,
    major:string,
    university:string,
    year_graduated:number
}

export interface Experience {
    company:string,
    position:string,
    duration_years:number
}

export interface Skills {
    skill:string,
    level:number
}

export interface Projects {
    project:string,
    description:string,
    duration_months:number
}

export interface UserProfileDataFromServer {
    name: string;
    gender: string;
    age: number;
    bio: string;
    current_occupation: CurrentOccupation;
    education:Education[];
    experience:Experience[];
    skills:Skills[];
    projects:Projects[];
}


export interface CriteriaSpecificScoring {
    criteria: string;
    score:number;
    reason:string;
    key_phrases_from_conversation: string[];
}

export interface EvaluationOutputMessage {
    criteria_specific_scoring: CriteriaSpecificScoring[];
}

export interface ActivityProgressAnalysis {
    candidate_performance_summary:string;
    things_left_to_do_with_respect_to_question:string;
    percentage_of_question_solved:number;
}

export interface EvaluationDataFromServer {
    candidate_id:string;
    candidate_name:string;
    candidate_profile_image:string;
    candidate_profile:UserProfileDataFromServer;
    overall_score:number;
    overall_analysis:string;
    evaluation_output:EvaluationOutputMessage;
    code_from_candidate:string;
    activity_analysis:ActivityProgressAnalysis;
    transcript:MasterChatMessage[];
    panelist_feedback:string[];
    panelist_names:string[];
}


export interface CriteriaScoreVisualSummary {
    criteria:string;
    score:number;
    reason_bullets: string[];
    topics_covered: string[];
}
export interface CriteriaScoreVisualSummaryList {
    criteria_score_list: CriteriaScoreVisualSummary[];
}

export enum CodeDimensions {
    TIME_COMPLEXITY = "Time Complexity",
    CODE_LOGIC = "Logic",
    CODE_INTERPRETATION = "Code Interpretation",
    CODE_STYLE = "Code Style",
    CODE_CORRECTNESS = "Code Correctness",
    CODE_EFFICIENCY = "Code Efficiency",
    CODE_READABILITY = "Code Readability",
    CODE_REUSABILITY = "Code Reusability"
}

export interface CodeSubmissionVisualSummary {
    language:string;
    content: string;
}
export interface CodeDimensionSummary {
    name:string;
    comment:string;
    rating:string;
}

export interface CodeAnalysisVisualSummary {
    code_overall_summary:string[];
    code_dimension_summary: CodeDimensionSummary[];
    completion_percentage: number 
}

export interface PanelistFeedbackVisualSummary {
    name: string
    role: string
    summary_bullets:string[]
}

export interface PanelistFeedbackVisualSummaryList {
    panelist_feedback: PanelistFeedbackVisualSummary[];
}

export interface OverallVisualSummary {
    score_label: string;
    key_insights: string[];
}

export interface CandidateEvaluationVisualisationReport {
    candidate_id: string;
    candidate_name: string;
    candidate_profile_image: string
    overall_score: number
    overall_visual_summary: OverallVisualSummary;
    criteria_scores: CriteriaScoreVisualSummary[]
    code_submission: CodeSubmissionVisualSummary
    code_analysis: CodeAnalysisVisualSummary
    panelist_feedback: PanelistFeedbackVisualSummary[]
    transcript: MasterChatMessage[]
    candidate_profile: UserProfileDataFromServer
}
