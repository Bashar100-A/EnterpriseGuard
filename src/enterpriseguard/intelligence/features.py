"""
EnterpriseGuard - Feature Extraction Layer
===========================================


Responsible for:


    - Converting security telemetry into ML-ready features
    - Validating feature values
    - Normalizing compatible telemetry
    - Maintaining the EnterpriseGuard ML feature contract


Feature Contract
----------------


The current EnterpriseGuard ML model expects exactly these 7 features:


    1. request_frequency
    2. failure_ratio
    3. unique_source_count
    4. unique_user_count
    5. failed_attempts
    6. anomaly_score
    7. outbound_data_volume


This module does NOT perform threat detection.
It only extracts and normalizes features.


Architecture:


    Raw Telemetry
         |
         v
    FeatureExtractor
         |
         v
    FeatureVector
         |
         v
    EnterpriseGuardModel
         |
         v
    ThreatDetector
"""


from __future__ import annotations


from dataclasses import dataclass
from math import isfinite, log1p
from typing import Any, Dict, Mapping




# ============================================================================
# FEATURE CONTRACT
# ============================================================================




FEATURE_NAMES = [
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
]




FEATURE_COUNT = len(FEATURE_NAMES)




# ============================================================================
# DATA MODEL
# ============================================================================




@dataclass(frozen=True)
class FeatureVector:
    """
    ML-ready EnterpriseGuard feature vector.


    The order of fields MUST remain synchronized with FEATURE_NAMES.
    """


    request_frequency: float = 0.0
    failure_ratio: float = 0.0
    unique_source_count: float = 0.0
    unique_user_count: float = 0.0
    failed_attempts: float = 0.0
    anomaly_score: float = 0.0
    outbound_data_volume: float = 0.0


    def to_dict(self) -> Dict[str, float]:
        """Return features as a dictionary."""


        return {
            "request_frequency": self.request_frequency,
            "failure_ratio": self.failure_ratio,
            "unique_source_count": self.unique_source_count,
            "unique_user_count": self.unique_user_count,
            "failed_attempts": self.failed_attempts,
            "anomaly_score": self.anomaly_score,
            "outbound_data_volume": self.outbound_data_volume,
        }


    def to_list(self) -> list[float]:
        """
        Return features in the official EnterpriseGuard order.
        """


        return [
            self.request_frequency,
            self.failure_ratio,
            self.unique_source_count,
            self.unique_user_count,
            self.failed_attempts,
            self.anomaly_score,
            self.outbound_data_volume,
        ]


    @property
    def feature_names(self) -> list[str]:
        """Return the official feature names."""


        return list(FEATURE_NAMES)


    def validate_contract(self) -> bool:
        """Verify that the vector matches the EnterpriseGuard contract."""


        return len(self.to_list()) == FEATURE_COUNT




# ============================================================================
# FEATURE EXTRACTOR
# ============================================================================




class FeatureExtractor:
    """
    Converts security telemetry into the EnterpriseGuard ML feature contract.


    This class performs feature engineering only.


    It does NOT:
        - classify threats
        - calculate final risk
        - make blocking decisions
        - train the ML model
    """


    VERSION = "2.0.0"


    def __init__(
        self,
        *,
        frequency_scale: float = 100.0,
        source_scale: float = 50.0,
        user_scale: float = 50.0,
        outbound_volume_scale: float = 100_000_000.0,
    ) -> None:


        if frequency_scale <= 0:
            raise ValueError("frequency_scale must be greater than zero")


        if source_scale <= 0:
            raise ValueError("source_scale must be greater than zero")


        if user_scale <= 0:
            raise ValueError("user_scale must be greater than zero")


        if outbound_volume_scale <= 0:
            raise ValueError(
                "outbound_volume_scale must be greater than zero"
            )


        self.frequency_scale = frequency_scale
        self.source_scale = source_scale
        self.user_scale = user_scale
        self.outbound_volume_scale = outbound_volume_scale


    # ------------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------------


    def extract(
        self,
        telemetry: Mapping[str, Any],
    ) -> FeatureVector:
        """
        Convert raw security telemetry into an ML-ready FeatureVector.


        Supported telemetry examples:


            {
                "request_count": 95,
                "failed_attempts": 8,
                "total_attempts": 10,
                "unique_source_ips": 30,
                "unique_user_count": 20,
                "anomaly_score": 0.75,
                "outbound_data_volume": 1000000
            }


        Aliases are supported for compatibility with different
        telemetry producers.
        """


        if not isinstance(telemetry, Mapping):
            raise TypeError(
                "telemetry must be a mapping/dictionary"
            )


        failed_attempts = self._non_negative_number(
            self._first_value(
                telemetry,
                "failed_attempts",
                "failed_authentication_attempts",
                "failed_requests",
            )
        )


        total_attempts = self._non_negative_number(
            self._first_value(
                telemetry,
                "total_attempts",
                "attempt_count",
                "total_requests",
            )
        )


        request_count = self._non_negative_number(
            self._first_value(
                telemetry,
                "request_count",
                "requests",
                "request_frequency",
            )
        )


        unique_sources = self._non_negative_number(
            self._first_value(
                telemetry,
                "unique_source_ips",
                "unique_sources",
                "unique_source_count",
            )
        )


        unique_users = self._non_negative_number(
            self._first_value(
                telemetry,
                "unique_user_count",
                "unique_users",
                "unique_accounts",
                "unique_user_ids",
            )
        )


        anomaly_score = self._clamp(
            self._first_value(
                telemetry,
                "anomaly_score",
                "behavioral_anomaly_score",
            )
        )


        outbound_volume = self._non_negative_number(
            self._first_value(
                telemetry,
                "outbound_data_volume",
                "bytes_transferred",
                "outbound_bytes",
                "data_volume",
            )
        )


        vector = FeatureVector(
            request_frequency=self._frequency(
                request_count
            ),
            failure_ratio=self._ratio(
                failed_attempts,
                total_attempts,
            ),
            unique_source_count=self._count_feature(
                unique_sources,
                self.source_scale,
            ),
            unique_user_count=self._count_feature(
                unique_users,
                self.user_scale,
            ),
            failed_attempts=failed_attempts,
            anomaly_score=anomaly_score,
            outbound_data_volume=self._data_volume(
                outbound_volume
            ),
        )


        if not vector.validate_contract():
            raise RuntimeError(
                "Feature vector does not match the EnterpriseGuard "
                "ML feature contract."
            )


        return vector


    # ------------------------------------------------------------------------
    # CONTRACT
    # ------------------------------------------------------------------------


    @staticmethod
    def get_feature_names() -> list[str]:
        """Return the canonical feature names."""


        return list(FEATURE_NAMES)


    @staticmethod
    def get_feature_count() -> int:
        """Return the canonical feature count."""


        return FEATURE_COUNT


    # ------------------------------------------------------------------------
    # NORMALIZATION
    # ------------------------------------------------------------------------


    @staticmethod
    def _clamp(
        value: Any,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:
        """Clamp a numeric value to a safe range."""


        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return minimum


        if not isfinite(numeric):
            return minimum


        return max(
            minimum,
            min(maximum, numeric),
        )


    @staticmethod
    def _non_negative_number(value: Any) -> float:
        """Convert a value into a finite non-negative number."""


        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0


        if not isfinite(numeric):
            return 0.0


        return max(0.0, numeric)


    def _frequency(self, value: Any) -> float:
        """
        Normalize request frequency using logarithmic scaling.


        This prevents very large request counts from dominating
        the feature vector.
        """


        numeric = self._non_negative_number(value)


        normalized = (
            log1p(numeric)
            / log1p(self.frequency_scale)
        )


        return self._clamp(normalized)


    @staticmethod
    def _ratio(
        numerator: Any,
        denominator: Any,
    ) -> float:
        """Calculate a safe normalized ratio."""


        try:
            numerator_value = max(
                0.0,
                float(numerator),
            )


            denominator_value = max(
                0.0,
                float(denominator),
            )
        except (TypeError, ValueError):
            return 0.0


        if denominator_value <= 0.0:
            return 0.0


        return min(
            numerator_value / denominator_value,
            1.0,
        )


    @staticmethod
    def _count_feature(
        value: Any,
        scale: float,
    ) -> float:
        """
        Normalize entity counts using logarithmic scaling.
        """


        try:
            numeric = max(
                0.0,
                float(value),
            )
        except (TypeError, ValueError):
            numeric = 0.0


        normalized = (
            log1p(numeric)
            / log1p(scale)
        )


        return max(
            0.0,
            min(1.0, normalized),
        )


    def _data_volume(self, value: Any) -> float:
        """
        Normalize outbound data volume.


        Higher values indicate larger outbound traffic.
        """


        numeric = self._non_negative_number(value)


        normalized = (
            log1p(numeric)
            / log1p(self.outbound_volume_scale)
        )


        return self._clamp(normalized)


    # ------------------------------------------------------------------------
    # TELEMETRY HELPERS
    # ------------------------------------------------------------------------


    @staticmethod
    def _first_value(
        telemetry: Mapping[str, Any],
        *names: str,
    ) -> Any:
        """
        Return the first available telemetry value.


        This allows different EnterpriseGuard components to use
        compatible field names without breaking the feature contract.
        """


        for name in names:
            if name in telemetry:
                return telemetry[name]


        return 0.0


    # ------------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------------


    def get_status(self) -> Dict[str, Any]:
        """Return feature extractor status."""


        return {
            "component": "EnterpriseGuard Feature Extractor",
            "version": self.VERSION,
            "feature_count": FEATURE_COUNT,
            "feature_names": list(FEATURE_NAMES),
            "contract_valid": True,
        }




# ============================================================================
# GLOBAL FEATURE EXTRACTOR
# ============================================================================




feature_extractor = FeatureExtractor()




# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================




def extract_features(
    telemetry: Mapping[str, Any],
) -> Dict[str, float]:
    """
    Extract ML-ready features from telemetry.


    Returns a dictionary suitable for EnterpriseGuard's
    model and detector layers.
    """


    return feature_extractor.extract(
        telemetry
    ).to_dict()




# ============================================================================
# SELF TEST
# ============================================================================




def _self_test() -> None:
    """Verify the feature extraction layer."""


    telemetry = {
        "request_count": 95,
        "failed_attempts": 8,
        "total_attempts": 10,
        "unique_source_ips": 30,
        "unique_user_count": 20,
        "anomaly_score": 0.75,
        "outbound_data_volume": 10_000_000,
    }


    vector = feature_extractor.extract(
        telemetry
    )


    print("=" * 78)
    print("EnterpriseGuard Feature Extraction Layer - Self Test")
    print("=" * 78)


    print("\n[1] Extracted feature vector")


    print(
        vector.to_list()
    )


    print("\n[2] Feature dictionary")


    print(
        vector.to_dict()
    )


    print("\n[3] Feature contract")


    print({
        "feature_count": FEATURE_COUNT,
        "feature_names": FEATURE_NAMES,
        "vector_length": len(vector.to_list()),
        "contract_valid": vector.validate_contract(),
    })


    print("\n[4] Extractor status")


    print(
        feature_extractor.get_status()
    )


    print("\n[5] Contract verification")


    assert len(vector.to_list()) == FEATURE_COUNT
    assert vector.validate_contract()


    assert list(vector.to_dict().keys()) == FEATURE_NAMES


    print({
        "status": "PASS",
        "message": (
            "Feature extraction contract matches "
            "EnterpriseGuard ML model contract."
        ),
    })


    print("\n" + "=" * 78)
    print("Feature extraction self test completed successfully.")
    print("=" * 78)




if __name__ == "__main__":
    _self_test()