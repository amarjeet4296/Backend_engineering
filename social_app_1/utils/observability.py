"""
Observability utilities for tracking and monitoring AI agents.
Implements integrations with LangSmith and Langfuse for end-to-end AI observability.
"""

import logging
import os
import time
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if LangSmith is available
try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning("LangSmith not available. Install with 'pip install langsmith'")

# Check if Langfuse is available
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.warning("Langfuse not available. Install with 'pip install langfuse'")


class ObservabilityTracker:
    """
    Utility for tracking and monitoring AI agent actions and performance.
    Provides integrations with LangSmith and Langfuse for comprehensive observability.
    """
    
    def __init__(self):
        """
        Initialize the observability tracker with available monitoring tools.
        """
        # Set up LangSmith if available
        self.langsmith_client = None
        self.langsmith_enabled = False
        
        if LANGSMITH_AVAILABLE:
            langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
            if langsmith_api_key:
                try:
                    self.langsmith_client = LangSmithClient()
                    self.langsmith_enabled = True
                    logger.info("LangSmith integration enabled")
                except Exception as e:
                    logger.warning(f"Failed to initialize LangSmith: {str(e)}")
        
        # Set up Langfuse if available
        self.langfuse_client = None
        self.langfuse_enabled = False
        
        if LANGFUSE_AVAILABLE:
            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            
            if langfuse_public_key and langfuse_secret_key:
                try:
                    self.langfuse_client = Langfuse(
                        public_key=langfuse_public_key,
                        secret_key=langfuse_secret_key,
                        host=langfuse_host
                    )
                    self.langfuse_enabled = True
                    logger.info("Langfuse integration enabled")
                except Exception as e:
                    logger.warning(f"Failed to initialize Langfuse: {str(e)}")
        
        # Set up internal tracking if external services are not available
        self.current_trace_id = None
        self.current_span_id = None
        self.traces = {}
        self.spans = {}
        
        logger.info("ObservabilityTracker initialized")

    @contextmanager
    def start_trace(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start a new trace for tracking a complete workflow.
        
        Args:
            name: Name of the trace
            metadata: Optional metadata for the trace
            
        Yields:
            None
        """
        trace_id = f"trace_{int(time.time() * 1000)}_{name}"
        start_time = time.time()
        
        # Log trace start
        logger.info(f"Starting trace: {name} (ID: {trace_id})")
        
        # Store the current trace ID
        previous_trace_id = self.current_trace_id
        self.current_trace_id = trace_id
        
        # Create trace in LangSmith if enabled
        langsmith_trace = None
        if self.langsmith_enabled:
            try:
                langsmith_trace = self.langsmith_client.create_run(
                    name=name,
                    inputs=metadata or {},
                )
            except Exception as e:
                logger.warning(f"Failed to create LangSmith trace: {str(e)}")
        
        # Create trace in Langfuse if enabled
        langfuse_trace = None
        if self.langfuse_enabled:
            try:
                langfuse_trace = self.langfuse_client.trace(
                    name=name,
                    metadata=metadata or {},
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse trace: {str(e)}")
        
        # Store trace information
        self.traces[trace_id] = {
            "name": name,
            "metadata": metadata or {},
            "start_time": start_time,
            "end_time": None,
            "spans": [],
            "langsmith_trace": langsmith_trace,
            "langfuse_trace": langfuse_trace
        }
        
        try:
            # Yield control back to the caller
            yield
        finally:
            # Record trace end
            end_time = time.time()
            self.traces[trace_id]["end_time"] = end_time
            duration = end_time - start_time
            
            # Log trace end
            logger.info(f"Completed trace: {name} (ID: {trace_id}) in {duration:.2f}s")
            
            # Update LangSmith if enabled
            if self.langsmith_enabled and langsmith_trace:
                try:
                    self.langsmith_client.update_run(
                        langsmith_trace.id,
                        outputs={"duration": duration},
                        end_time=end_time
                    )
                except Exception as e:
                    logger.warning(f"Failed to update LangSmith trace: {str(e)}")
            
            # Update Langfuse if enabled
            if self.langfuse_enabled and langfuse_trace:
                try:
                    langfuse_trace.update(
                        metadata={"duration": duration}
                    )
                    langfuse_trace.end()
                except Exception as e:
                    logger.warning(f"Failed to update Langfuse trace: {str(e)}")
            
            # Restore previous trace ID
            self.current_trace_id = previous_trace_id

    @contextmanager
    def start_span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start a new span within the current trace for tracking a specific operation.
        
        Args:
            name: Name of the span
            metadata: Optional metadata for the span
            
        Yields:
            None
        """
        span_id = f"span_{int(time.time() * 1000)}_{name}"
        start_time = time.time()
        
        # Log span start
        logger.debug(f"Starting span: {name} (ID: {span_id})")
        
        # Store the current span ID
        previous_span_id = self.current_span_id
        self.current_span_id = span_id
        
        # Create span in LangSmith if enabled and we have a trace
        langsmith_span = None
        if self.langsmith_enabled and self.current_trace_id and self.traces.get(self.current_trace_id):
            langsmith_trace = self.traces[self.current_trace_id].get("langsmith_trace")
            if langsmith_trace:
                try:
                    langsmith_span = self.langsmith_client.create_run(
                        name=name,
                        inputs=metadata or {},
                        parent_run_id=langsmith_trace.id
                    )
                except Exception as e:
                    logger.warning(f"Failed to create LangSmith span: {str(e)}")
        
        # Create span in Langfuse if enabled and we have a trace
        langfuse_span = None
        if self.langfuse_enabled and self.current_trace_id and self.traces.get(self.current_trace_id):
            langfuse_trace = self.traces[self.current_trace_id].get("langfuse_trace")
            if langfuse_trace:
                try:
                    langfuse_span = langfuse_trace.span(
                        name=name,
                        metadata=metadata or {},
                    )
                except Exception as e:
                    logger.warning(f"Failed to create Langfuse span: {str(e)}")
        
        # Store span information
        self.spans[span_id] = {
            "name": name,
            "trace_id": self.current_trace_id,
            "metadata": metadata or {},
            "start_time": start_time,
            "end_time": None,
            "langsmith_span": langsmith_span,
            "langfuse_span": langfuse_span
        }
        
        # Add span to trace if we have a current trace
        if self.current_trace_id and self.current_trace_id in self.traces:
            self.traces[self.current_trace_id]["spans"].append(span_id)
        
        try:
            # Yield control back to the caller
            yield
        finally:
            # Record span end
            end_time = time.time()
            self.spans[span_id]["end_time"] = end_time
            duration = end_time - start_time
            
            # Log span end
            logger.debug(f"Completed span: {name} (ID: {span_id}) in {duration:.2f}s")
            
            # Update LangSmith if enabled
            if self.langsmith_enabled and langsmith_span:
                try:
                    self.langsmith_client.update_run(
                        langsmith_span.id,
                        outputs={"duration": duration},
                        end_time=end_time
                    )
                except Exception as e:
                    logger.warning(f"Failed to update LangSmith span: {str(e)}")
            
            # Update Langfuse if enabled
            if self.langfuse_enabled and langfuse_span:
                try:
                    langfuse_span.update(
                        metadata={"duration": duration}
                    )
                    langfuse_span.end()
                except Exception as e:
                    logger.warning(f"Failed to update Langfuse span: {str(e)}")
            
            # Restore previous span ID
            self.current_span_id = previous_span_id

    def log_event(self, name: str, event_type: str, data: Dict[str, Any] = None):
        """
        Log an event within the current trace or span.
        
        Args:
            name: Name of the event
            event_type: Type of event (e.g., 'info', 'warning', 'error')
            data: Event data
        """
        event_time = time.time()
        
        # Log the event
        log_message = f"Event: {name} (Type: {event_type})"
        if data:
            log_message += f" - Data: {data}"
            
        if event_type == 'error':
            logger.error(log_message)
        elif event_type == 'warning':
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Log event in LangSmith if enabled and we have a current span or trace
        if self.langsmith_enabled:
            if self.current_span_id and self.spans.get(self.current_span_id):
                langsmith_span = self.spans[self.current_span_id].get("langsmith_span")
                if langsmith_span:
                    try:
                        self.langsmith_client.create_feedback(
                            run_id=langsmith_span.id,
                            key=event_type,
                            value=name,
                            comment=str(data) if data else None
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log LangSmith event: {str(e)}")
            elif self.current_trace_id and self.traces.get(self.current_trace_id):
                langsmith_trace = self.traces[self.current_trace_id].get("langsmith_trace")
                if langsmith_trace:
                    try:
                        self.langsmith_client.create_feedback(
                            run_id=langsmith_trace.id,
                            key=event_type,
                            value=name,
                            comment=str(data) if data else None
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log LangSmith event: {str(e)}")
        
        # Log event in Langfuse if enabled and we have a current span or trace
        if self.langfuse_enabled:
            if self.current_span_id and self.spans.get(self.current_span_id):
                langfuse_span = self.spans[self.current_span_id].get("langfuse_span")
                if langfuse_span:
                    try:
                        langfuse_span.event(
                            name=name,
                            metadata=data or {}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log Langfuse event: {str(e)}")
            elif self.current_trace_id and self.traces.get(self.current_trace_id):
                langfuse_trace = self.traces[self.current_trace_id].get("langfuse_trace")
                if langfuse_trace:
                    try:
                        langfuse_trace.event(
                            name=name,
                            metadata=data or {}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log Langfuse event: {str(e)}")

    def log_model_usage(self, model_name: str, prompt_tokens: int, completion_tokens: int, metadata: Dict[str, Any] = None):
        """
        Log LLM model usage for cost tracking and performance monitoring.
        
        Args:
            model_name: Name of the model used
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            metadata: Additional metadata
        """
        total_tokens = prompt_tokens + completion_tokens
        
        # Log model usage
        logger.info(f"Model usage: {model_name} - Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total: {total_tokens}")
        
        # Log in LangSmith and Langfuse if applicable
        usage_data = {
            "model": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            **(metadata or {})
        }
        
        self.log_event(f"model_usage_{model_name}", "usage", usage_data)

    def get_trace_summary(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of a specific trace or the current trace.
        
        Args:
            trace_id: Optional trace ID to get summary for
            
        Returns:
            Dictionary with trace summary
        """
        if not trace_id and not self.current_trace_id:
            logger.warning("No active trace to summarize")
            return {}
            
        trace_id = trace_id or self.current_trace_id
        
        if trace_id not in self.traces:
            logger.warning(f"Trace {trace_id} not found")
            return {}
            
        trace = self.traces[trace_id]
        
        # Calculate total duration
        duration = None
        if trace["end_time"] and trace["start_time"]:
            duration = trace["end_time"] - trace["start_time"]
            
        # Get span information
        spans = []
        for span_id in trace["spans"]:
            if span_id in self.spans:
                span = self.spans[span_id]
                span_duration = None
                if span["end_time"] and span["start_time"]:
                    span_duration = span["end_time"] - span["start_time"]
                
                spans.append({
                    "name": span["name"],
                    "duration": span_duration,
                    "metadata": span["metadata"]
                })
        
        # Create summary
        return {
            "name": trace["name"],
            "duration": duration,
            "metadata": trace["metadata"],
            "spans": spans,
            "span_count": len(spans)
        }
