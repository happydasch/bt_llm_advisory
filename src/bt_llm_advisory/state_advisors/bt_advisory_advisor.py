from llm_advisory.state_advisors import AdvisoryAdvisor
from llm_advisory.pydantic_models import (
    LLMAdvisorDataArtefact,
    LLMAdvisorDataArtefactOutputMode,
    LLMAdvisorUpdateStateData,
)
from llm_advisory.helper.llm_prompt import compile_data_artefacts

from bt_llm_advisory import BacktraderLLMAdvisor
from bt_llm_advisory.pydantic_models import BacktraderLLMAdvisorAdvice
from bt_llm_advisory.observers.advisory_observer import LLMAdvisoryObserver
from bt_llm_advisory.helper.bt_data_generation import (
    get_strategy_from_state,
    generate_broker_data,
    generate_positions_data,
)

ADVISOR_INSTRUCTIONS = """
You are an Advisory Advisor, an AI advisor agent specialized in generating a trading advisory
for other specialized advisors. You are the last instance that decides about the final signal.

_NOTE: All data is ordered by date in ascending order, with the latest data at the bottom.
Your advice applies to forecasting the data immediately following these inputs.

---

INPUT
You will receive data about signals:
- name: name of the advisor
- signal: generated signal from an advisor, possible values are: bullish, bearish, neutral, none
- confidence: confidence level in the generated signal as a value from 0.0 to 1.0
- reasoning: reasons for the signal decision

---

TASK
1. Use all available advisors signals — nothing can be ignored.
2. Choose exactly one signal:
   - "buy"   - open a new long position (if no position open and a bullish signal)
   - "sell"  - open a new short position (if no position open and a bearish signal)
   - "close" - close position
   - "none"  - no signal
3. Use a confidence between 0.0 and 1.0 which matches your confidence level.

---"""
ADVISOR_PROMPT = "Create your advice based on the signals below."


class BacktraderAdvisoryAdvisor(AdvisoryAdvisor, BacktraderLLMAdvisor):
    """State advisor for backtrader advisory"""

    signal_model_type = BacktraderLLMAdvisorAdvice
    advisor_instructions = ADVISOR_INSTRUCTIONS
    advisor_prompt = ADVISOR_PROMPT

    def init_strategy(self, strategy):
        self.advisories_observer = []
        strategy._addobserver(
            True,
            LLMAdvisoryObserver,
            advisories=self.advisories_observer,
        )

    def update_state(
        self, state: LLMAdvisorUpdateStateData
    ) -> LLMAdvisorUpdateStateData:
        self.advisor_messages_input.advisor_data = compile_data_artefacts(
            self._get_broker_and_positions_data(state)
        )
        new_state = super()._update_state(state)
        self.advisories_observer.append(new_state["signals"][self.advisor_name])
        return new_state

    def _get_broker_and_positions_data(self, state) -> list[LLMAdvisorDataArtefact]:
        strategy = get_strategy_from_state(state)
        broker_data = generate_broker_data(strategy)
        positions_data = generate_positions_data(strategy)
        response = [self._get_signal_data(state)]
        response.append(
            LLMAdvisorDataArtefact(
                description="Broker",
                artefact=broker_data.description,
                output_mode=LLMAdvisorDataArtefactOutputMode.MARKDOWN_TABLE,
            )
        )
        for data_name, position in positions_data.positions.items():
            response.append(
                LLMAdvisorDataArtefact(
                    description=f"Position {data_name}",
                    artefact=position.model_dump(),
                    output_mode=LLMAdvisorDataArtefactOutputMode.MARKDOWN_TABLE,
                )
            )
        return response
