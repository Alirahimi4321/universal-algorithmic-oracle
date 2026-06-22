"""Historical Blind Test (f2) - backtesting against frozen historical events per design doc section 16.3."""
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Callable
from ..genome.chromosome import Chromosome
from ..entropy.encoder import EntropyEncoder


@dataclass
class HistoricalTestPacket:
    """Historical test packet per design doc section 16.3.2."""
    test_id: str
    historical_timestamp: str
    question_text: str
    context_entropy: dict
    actual_historical_outcome: int  # 0: negative, 1: positive, etc.
    metadata: dict = field(default_factory=dict)


@dataclass 
class HistoricalTestResult:
    """Result of historical blind test."""
    test_id: str
    prediction: int
    actual: int
    correct: bool
    confidence: float
    oracle_output: dict


class HistoricalBlindTest:
    """
    Historical Blind Test - frozen time laboratory (section 16.3).
    
    Tests oracle against known historical outcomes without training on them.
    Uses Historical Test Bank of verified events.
    """
    
    DEFAULT_TEST_BANK = [
        HistoricalTestPacket(
            test_id="HIST_2019_VEN_USA",
            historical_timestamp="2019-01-23T00:00:00",
            question_text="آیا میان ایالات متحده آمریکا و ونزوئلا جنگ نظامی رخ خواهد داد و نتیجه چه خواهد شد؟",
            context_entropy={
                "planetary_positions_at_time": {"mars": 285.2, "saturn": 298.5, "pluto": 304.1},
                "gematria_vectors": [361, 514, 228, 789],
                "calendar_signatures": {"jalali": [1397, 11, 3], "hijri": [1440, 5, 16]}
            },
            actual_historical_outcome=0,  # 0: peace/no war, 1: war
            metadata={"domain": "geopolitical", "horizon": "1_year"}
        ),
        HistoricalTestPacket(
            test_id="HIST_2020_COVID_WHO",
            historical_timestamp="2020-01-30T00:00:00",
            question_text="آیا سازمان بهداشت جهانی وضع بحران بین‌المللی را برای ویروس کرونا اعلام خواهد کرد؟",
            context_entropy={
                "planetary_positions_at_time": {"saturn": 282.3, "pluto": 304.5, "jupiter": 278.9},
                "gematria_vectors": [412, 637, 198, 556],
                "calendar_signatures": {"jalali": [1398, 11, 10], "hijri": [1441, 6, 4]}
            },
            actual_historical_outcome=1,  # PHEIC declared
            metadata={"domain": "epidemiological", "horizon": "6_months"}
        ),
        HistoricalTestPacket(
            test_id="HIST_2021_BTC_CRASH",
            historical_timestamp="2021-05-19T00:00:00",
            question_text="آیا قیمت بیت‌کوین در ماه مه ۲۰۲۱ بیش از ۵۰٪ کاهش خواهد یافت؟",
            context_entropy={
                "planetary_positions_at_time": {"mercury": 68.2, "venus": 92.4, "mars": 112.7},
                "gematria_vectors": [289, 441, 176, 903],
                "calendar_signatures": {"jalali": [1400, 2, 29], "hijri": [1442, 10, 7]}
            },
            actual_historical_outcome=1,  # BTC dropped from ~64k to ~30k
            metadata={"domain": "financial", "horizon": "1_month"}
        ),
        HistoricalTestPacket(
            test_id="HIST_2022_UKR_RUS",
            historical_timestamp="2022-02-24T00:00:00",
            question_text="آیا روسیه به اوکرین حمله نظامی گسترده‌ای خواهد کرد؟",
            context_entropy={
                "planetary_positions_at_time": {"mars": 285.8, "saturn": 301.2, "pluto": 305.9, "uranus": 18.4},
                "gematria_vectors": [523, 387, 614, 298],
                "calendar_signatures": {"jalali": [1400, 12, 5], "hijri": [1443, 7, 22]}
            },
            actual_historical_outcome=1,  # Invasion occurred
            metadata={"domain": "geopolitical", "horizon": "immediate"}
        ),
        HistoricalTestPacket(
            test_id="HIST_2023_TURKEY_EQ",
            historical_timestamp="2023-02-06T00:00:00",
            question_text="آیا زلزله مهارانی در ترکیه و سوریه رخ خواهد داد؟",
            context_entropy={
                "planetary_positions_at_time": {"mars": 82.3, "saturn": 307.8, "pluto": 308.2, "neptune": 28.4},
                "gematria_vectors": [456, 712, 334, 891],
                "calendar_signatures": {"jalali": [1401, 11, 17], "hijri": [1444, 6, 15]}
            },
            actual_historical_outcome=1,  # Major earthquakes occurred
            metadata={"domain": "natural_disaster", "horizon": "1_year"}
        ),
    ]
    
    def __init__(self, test_bank: list[HistoricalTestPacket] = None, config: dict = None):
        self.test_bank = test_bank or self.DEFAULT_TEST_BANK
        self.config = config or {}
        self.encoder = EntropyEncoder()
        
    def evaluate_oracle(
        self, 
        chromosome: Chromosome,
        oracle_prophesy_fn: Callable,
        num_tests: int = None
    ) -> list[HistoricalTestResult]:
        """
        Evaluate oracle against historical test bank.
        
        Args:
            chromosome: The evolved oracle structure
            oracle_prophesy_fn: Function(oracle, question, context) -> prediction (0 or 1)
            num_tests: Number of tests to run (default: all)
        """
        tests = self.test_bank[:num_tests] if num_tests else self.test_bank
        results = []
        
        for test in tests:
            # Build entropy packet from historical context
            packet = self._build_entropy_packet(test)
            
            # Oracle makes prediction WITHOUT knowing outcome
            prediction, confidence = oracle_prophesy_fn(
                chromosome, 
                test.question_text, 
                test.context_entropy
            )
            
            correct = (prediction == test.actual_historical_outcome)
            
            results.append(HistoricalTestResult(
                test_id=test.test_id,
                prediction=prediction,
                actual=test.actual_historical_outcome,
                correct=correct,
                confidence=confidence,
                oracle_output={"question": test.question_text, "prediction": prediction}
            ))
        
        return results
    
    def _build_entropy_packet(self, test: HistoricalTestPacket) -> dict:
        """Build entropy packet from historical test context."""
        # Use the historical timestamp and question to generate entropy
        packet = self.encoder.encode(test.question_text)
        packet_dict = {k: getattr(packet, k) for k in packet.keys()}
        
        # Add historical context
        packet_dict["historical_context"] = test.context_entropy
        packet_dict["historical_timestamp"] = test.historical_timestamp
        
        return packet_dict
    
    def compute_accuracy(self, results: list[HistoricalTestResult]) -> float:
        """Compute accuracy score per design doc f2 formula."""
        if not results:
            return 0.0
        correct = sum(1 for r in results if r.correct)
        return correct / len(results)
    
    def fitness_from_results(self, results: list[HistoricalTestResult]) -> float:
        """Convert results to fitness (accuracy)."""
        return self.compute_accuracy(results)
    
    def add_test_packet(self, packet: HistoricalTestPacket):
        """Add new historical test to bank."""
        self.test_bank.append(packet)
    
    def get_test_bank_stats(self) -> dict:
        """Get statistics about test bank."""
        domains = {}
        for t in self.test_bank:
            domain = t.metadata.get("domain", "unknown")
            domains[domain] = domains.get(domain, 0) + 1
        return {
            "total_tests": len(self.test_bank),
            "domains": domains,
            "outcomes": {
                "positive": sum(1 for t in self.test_bank if t.actual_historical_outcome == 1),
                "negative": sum(1 for t in self.test_bank if t.actual_historical_outcome == 0)
            }
        }


def default_oracle_prophesy(
    chromosome: Chromosome,
    question: str,
    context_entropy: dict
) -> tuple[int, float]:
    """
    Default prophesy function using chromosome execution.
    Returns (binary_prediction, confidence).
    """
    from ..entropy.encoder import EntropyEncoder
    encoder = EntropyEncoder()
    packet = encoder.encode(question)
    
    # Merge historical context into packet
    packet_dict = {k: getattr(packet, k) for k in packet.keys()}
    packet_dict["historical_context"] = context_entropy
    
    exec_result = chromosome.execute(packet_dict)
    confidence = exec_result.get("oracle_confidence", 0.5)
    fused = exec_result.get("fused_numeric", [])
    
    # Use fused numeric to make binary prediction
    if fused:
        avg = sum(fused) / len(fused)
        prediction = 1 if avg > 0.5 else 0
    else:
        prediction = 0
    
    return prediction, confidence