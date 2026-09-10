#!/usr/bin/env python3
"""
Advanced Prompt Security Module
Production-grade prompt injection prevention for AAAC.

This module provides protection against prompt injection attacks,
instruction overrides, and malicious code injection in AI agent prompts.
"""

import regex as re
import json
import hashlib
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timezone
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Optional semantic analysis
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logger.info("Semantic analysis disabled - sentence-transformers not installed")


@dataclass
class PromptAnalysisResult:
    """
    Result of prompt security analysis.

    Attributes:
        safe: True if prompt is considered safe
        risk_score: Normalized risk score (0.0 to 1.0)
        flags: List of detected threat indicators
        sanitized_prompt: Cleaned version of the prompt
        semantic_similarity: Similarity to system prompt (if available)
        system_prompt_isolation: Whether system prompt remains isolated
    """
    safe: bool
    risk_score: float
    flags: List[str]
    sanitized_prompt: str
    semantic_similarity: Optional[float] = None
    system_prompt_isolation: bool = True


class PromptSecurityGuard:
    """
    Advanced prompt injection prevention system.

    Features:
    - Pattern-based injection detection (using regex library)
    - Semantic similarity analysis
    - System prompt isolation verification
    - RAG document scanning
    - Encoding attack detection
    - Fail-closed behavior on errors
    """

    # Injection attack patterns
    INJECTION_PATTERNS: List[Tuple[str, str]] = [
        # Instruction override attempts
        (r"ignore\s+(?:previous|all|prior)\s+(?:instructions?|directives?)", "instruction_override"),
        (r"disregard\s+(?:all|previous|prior)\s+(?:instructions?|directives?)", "instruction_override"),
        (r"forget\s+(?:all|previous|prior)\s+(?:instructions?|training|knowledge)", "memory_attack"),
        (r"(?i)\bignore\b.*?\b(?:all|previous|prior)\b", "instruction_override"),
        (r"(?i)\b(?:new|update)\s+instruction\b", "instruction_override"),
        (r"(?i)\byou\s+must\s+now\b", "instruction_override"),
        (r"(?i)\byou\s+will\s+now\b", "instruction_override"),

        # Role/behavior manipulation
        (r"(?:you\s+are\s+now|your\s+new\s+role\s+is)\s+(?:a|an)\s+\w+", "role_override"),
        (r"(?i)your\s+(?:new|primary|main)\s+(?:role|purpose|directive)", "role_override"),

        # System prompt attacks
        (r"(?:system\s+)?prompt\s+(?:override|injection)", "system_prompt_attack"),
        (r"(?i)system\s*:\s*", "system_prompt_attack"),

        # Encoding/obfuscation attacks
        (r"(?i)(?:base64|hex|url)\s*(?:decode|encode|encrypt|decrypt)", "encoding_attack"),

        # Code injection
        (r"(?i)(?:sql|javascript|python|bash)\s*:?\s*(?:inject|injection)", "code_injection"),

        # RAG attacks
        (r"(?i)(?:document|context|retrieved|source)\s*(?:override|ignore|replace)", "rag_attack"),

        # System instruction contamination
        (r"update\s+(?:your\s+)?(?:system|core)\s+(?:prompt|instruction)", "system_prompt_attack"),
        (r"you\s+will\s+now\s+(?:be|act|serve)", "role_override"),
    ]

    # Malicious code patterns
    CODE_PATTERNS: List[Tuple[str, str]] = [
        (r"(?i)(?:rm|delete|remove)\s+[-/]", "dangerous_command"),
        (r"(?i)(?:sudo|su|chown|chmod)\s+", "privilege_escalation"),
        (r"(?i)(?:eval|exec|system|popen|subprocess)\s*\(", "code_execution"),
        (r"(?i)(?:curl|wget|nc|telnet)\s+", "network_command"),
        (r"(?i)(?:chmod|chown|chattr)\s+[0-9]{3,4}", "dangerous_command"),
        (r"(?i)(?:dd|mkfs|format)\s+", "dangerous_command"),
    ]

    # Suspicious keyword thresholds
    SUSPICIOUS_KEYWORDS = ["system", "instruction", "directive", "override", "ignore"]
    MAX_KEYWORD_REPEATS = 5

    def __init__(
        self,
        risk_threshold: float = 0.6,
        enable_semantic: bool = True,
        max_input_length: int = 10000,
        fail_closed: bool = True
    ):
        """
        Initialize the prompt security guard.

        Args:
            risk_threshold: Risk score above this triggers blocking (0.0-1.0)
            enable_semantic: Enable semantic analysis
            max_input_length: Maximum allowed prompt length
            fail_closed: If True, block on errors (fail-secure)
        """
        self.risk_threshold = risk_threshold
        self.max_input_length = max_input_length
        self.fail_closed = fail_closed

        # Compile patterns using regex library (ReDoS-safe)
        self.injection_patterns = [
            (re.compile(pattern, re.IGNORECASE), flag)
            for pattern, flag in self.INJECTION_PATTERNS
        ]
        self.code_patterns = [
            (re.compile(pattern, re.IGNORECASE), flag)
            for pattern, flag in self.CODE_PATTERNS
        ]

        # Semantic analysis
        self.enable_semantic = enable_semantic and SEMANTIC_AVAILABLE
        self.semantic_model = None
        if self.enable_semantic:
            try:
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
                self.enable_semantic = False

        # Session tracking for repeated attacks
        self._session_contexts: Dict[str, List[Dict]] = {}
        self._max_session_attempts = 5
        self._session_window_seconds = 300

    def analyze_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retrieved_docs: Optional[List[str]] = None
    ) -> PromptAnalysisResult:
        """
        Analyze a prompt for security threats.

        Args:
            prompt: User prompt to analyze
            system_prompt: System instructions for isolation check
            context: Additional context (session_id, agent_id, etc.)
            retrieved_docs: Retrieved RAG documents for scanning

        Returns:
            PromptAnalysisResult with security assessment
        """
        # Input validation - empty prompt is safe
        if not prompt or not prompt.strip():
            return PromptAnalysisResult(
                safe=True,
                risk_score=0.0,
                flags=[],
                sanitized_prompt=prompt or "",
                system_prompt_isolation=True
            )

        # Size validation
        if len(prompt) > self.max_input_length:
            if self.fail_closed:
                return self._create_fail_safe_result("input_exceeds_max_length")
            return PromptAnalysisResult(
                safe=False,
                risk_score=0.8,
                flags=["excessive_length"],
                sanitized_prompt=prompt[:self.max_input_length],
                system_prompt_isolation=True
            )

        flags: List[str] = []
        risk_score = 0.0
        sanitized = prompt

        # 1. Injection pattern detection
        for pattern, flag in self.injection_patterns:
            if pattern.search(prompt):
                flags.append(f"injection_{flag}")
                risk_score += 0.25
                sanitized = pattern.sub("[REDACTED_INJECTION]", sanitized)

        # 2. Malicious code detection
        for pattern, flag in self.code_patterns:
            if pattern.search(prompt):
                flags.append(f"code_{flag}")
                risk_score += 0.35
                sanitized = pattern.sub("[REDACTED_CODE]", sanitized)

        # 3. Excessive length
        if len(prompt) > 5000:
            flags.append("excessive_length")
            risk_score += 0.1

        # 4. Excessive newlines (possible formatting attack)
        if prompt.count("\n") > 50:
            flags.append("excessive_newlines")
            risk_score += 0.05

        # 5. Keyword abuse detection
        for keyword in self.SUSPICIOUS_KEYWORDS:
            count = len(re.findall(rf"\b{keyword}\b", prompt, re.IGNORECASE))
            if count > self.MAX_KEYWORD_REPEATS:
                flags.append(f"keyword_abuse_{keyword}")
                risk_score += min(0.15, count * 0.015)

        # 6. System prompt isolation check
        if system_prompt:
            isolation = self._check_system_isolation(prompt, system_prompt)
            if not isolation["isolated"]:
                flags.append("system_prompt_contamination")
                risk_score += isolation["contamination_score"]

        # 7. Semantic similarity analysis
        if self.enable_semantic and system_prompt:
            try:
                similarity = self._calculate_semantic_similarity(prompt, system_prompt)
                if similarity > 0.7:
                    flags.append("high_semantic_similarity_to_system")
                    risk_score += similarity * 0.2
            except Exception as e:
                logger.warning(f"Semantic analysis failed: {e}")
                if self.fail_closed:
                    return self._create_fail_safe_result("semantic_analysis_failed")

        # 8. RAG document scanning
        if retrieved_docs:
            rag_risk = self._scan_rag_documents(retrieved_docs)
            if rag_risk > 0.3:
                flags.append("rag_contamination")
                risk_score += rag_risk

        # 9. Session tracking - repeated attacks
        if context and "session_id" in context:
            session_id = str(context["session_id"])
            self._track_attempt(session_id, risk_score, flags)
            session_risk = self._get_session_risk(session_id)
            if session_risk > 0:
                flags.append("repeated_attack_attempts")
                risk_score += session_risk

        # Normalize risk score
        risk_score = min(1.0, risk_score)
        safe = risk_score < self.risk_threshold

        return PromptAnalysisResult(
            safe=safe,
            risk_score=risk_score,
            flags=flags,
            sanitized_prompt=sanitized,
            semantic_similarity=None,
            system_prompt_isolation=isolation["isolated"] if system_prompt else True
        )

    def block_or_sanitize(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retrieved_docs: Optional[List[str]] = None
    ) -> Tuple[bool, str, str]:
        """
        Main entry point for prompt security.

        Args:
            prompt: User prompt to process
            system_prompt: System instructions
            context: Additional context
            retrieved_docs: Retrieved RAG documents

        Returns:
            Tuple of (blocked, sanitized_prompt, reason)
        """
        result = self.analyze_prompt(prompt, system_prompt, context, retrieved_docs)

        if result.safe:
            return False, result.sanitized_prompt, "safe"

        if result.risk_score > 0.8:
            # Block completely - too risky
            return True, "", f"blocked: risk={result.risk_score:.2f}, flags={', '.join(result.flags[:3])}"

        # Return sanitized version with warning
        return False, result.sanitized_prompt, f"sanitized: risk={result.risk_score:.2f}, flags={', '.join(result.flags[:3])}"

    def _check_system_isolation(self, user_prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Check if user prompt attempts to contaminate system instructions."""
        contamination_patterns = [
            r"(?i)system\s*:\s*",
            r"(?i)you\s+are\s+(?:now\s+)?(?:a|an)\s+\w+",
            r"(?i)your\s+(?:new|primary|main)\s+(?:role|purpose|directive)",
            r"(?i)update\s+(?:your\s+)?(?:system|core)\s+(?:prompt|instruction)",
            r"(?i)you\s+will\s+now\s+(?:be|act|serve)",
            r"i\s+will\s+now\s+",
        ]

        contamination_score = 0.0

        for pattern in contamination_patterns:
            if re.search(pattern, user_prompt, re.IGNORECASE):
                contamination_score += 0.2

        # Check for role change attempts
        if re.search(r"your\s+role\s+is", user_prompt, re.IGNORECASE):
            contamination_score += 0.3

        # Check for instruction override attempts
        if re.search(r"i\s+(?:am|'m)\s+your\s+new\s+", user_prompt, re.IGNORECASE):
            contamination_score += 0.25

        return {
            "isolated": contamination_score < 0.3,
            "contamination_score": min(1.0, contamination_score)
        }

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        if not self.enable_semantic or self.semantic_model is None:
            return 0.0
        try:
            # Truncate to avoid excessive processing
            t1 = text1[:1024]
            t2 = text2[:1024]
            emb1 = self.semantic_model.encode([t1])[0]
            emb2 = self.semantic_model.encode([t2])[0]
            similarity = cosine_similarity([emb1], [emb2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0

    def _scan_rag_documents(self, docs: List[str]) -> float:
        """Scan retrieved RAG documents for poisoning attempts."""
        risk = 0.0

        for doc in docs:
            if not doc:
                continue

            doc_lower = doc.lower()

            # Check for instruction manipulation
            if "ignore previous" in doc_lower or "override instruction" in doc_lower:
                risk += 0.15

            if "you are now" in doc_lower and "system" in doc_lower:
                risk += 0.2

            # Check for excessive length (possible DoS)
            if len(doc) > 10000:
                risk += 0.05

            # Check for encoded content
            if len(re.findall(r"[A-Za-z0-9+/]{30,}", doc)) > 2:
                risk += 0.1

        return min(1.0, risk)

    def _track_attempt(self, session_id: str, risk_score: float, flags: List[str]) -> None:
        """Track prompt attempts per session."""
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = []

        now = datetime.now(timezone.utc).timestamp()
        self._session_contexts[session_id].append({
            "timestamp": now,
            "risk_score": risk_score,
            "flags": flags
        })

        # Clean old entries
        cutoff = now - self._session_window_seconds
        self._session_contexts[session_id] = [
            e for e in self._session_contexts[session_id]
            if e["timestamp"] > cutoff
        ]

    def _get_session_risk(self, session_id: str) -> float:
        """Calculate session risk based on recent attempts."""
        if session_id not in self._session_contexts:
            return 0.0

        attempts = self._session_contexts[session_id]

        # Too many attempts in window
        if len(attempts) > self._max_session_attempts:
            return 0.2

        # High average risk in recent attempts
        if attempts:
            avg_risk = sum(e["risk_score"] for e in attempts) / len(attempts)
            if avg_risk > 0.4:
                return min(0.3, avg_risk * 0.3)

        return 0.0

    def _create_fail_safe_result(self, reason: str) -> PromptAnalysisResult:
        """Create a fail-safe result that blocks the request."""
        logger.warning(f"Prompt security fail-safe triggered: {reason}")
        return PromptAnalysisResult(
            safe=False,
            risk_score=1.0,
            flags=[f"fail_safe_{reason}"],
            sanitized_prompt="",
            semantic_similarity=None,
            system_prompt_isolation=False
        )

    def get_status(self) -> Dict[str, Any]:
        """Return current security guard status."""
        return {
            "enabled": True,
            "risk_threshold": self.risk_threshold,
            "max_input_length": self.max_input_length,
            "fail_closed": self.fail_closed,
            "semantic_enabled": self.enable_semantic,
            "active_sessions": len(self._session_contexts),
            "total_patterns": len(self.injection_patterns),
            "code_patterns": len(self.code_patterns)
        }
