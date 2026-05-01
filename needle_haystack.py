from dataclasses import asdict, dataclass, field
from typing import Literal
import random


@dataclass
class NeedleConfig:
    """Controls needle-level variables."""

    repetitions: list[int] = field(default_factory=lambda: [1, 1, 1])
    """Number of times a given needle appears in the haystack."""

    order: list[int] = field(default_factory=lambda: [0, 1, 2])
    """
    Order in which a particular needle appears in the document.
        0 = first needle, 1 = second needle, 2 = third needle.
        For example, [2, 0, 1] means the third needle appears first
    """


@dataclass
class HaystackConfig:
    """Controls haystack-level variables."""

    needle_set: str
    """Identifier of which needle set to use (e.g., "C1")."""

    question_domain: str
    """Domain of the question: geography / history / biology."""

    semantic_related: bool
    """Whether the haystack article domain matches the question domain."""

    max_words: int = 5000
    """Target haystack length in words (paper uses 5000)."""

    position: LayoutPosition = "middle"
    """General region of haystack where needles are inserted: beginning / middle / end / even."""

    grouping: LayoutGrouping = "sequential"
    """How close needles are: sequential or 5pct_apart (of total doc length)."""


# Default needle sets and questions (Table 1 of the paper — C1 configuration)
DEFAULT_NEEDLE_SETS = {
    "C1": {
        "needles": ["Dralveth", "Fyrundell", "Zequarith"],
        "questions": {
            "geography": "What is the capital of Xaltruvia?",
            "history": "Which treaty resolved the Xaltruvian conflict?",
            "biology": "In which genus is Xaltruvia classified?",
        },
        "needle_templates": {
            "geography": "The capital of Xaltruvia is {needle}.",
            "history": "The Xaltruvian conflict was resolved by the Treaty of {needle}.",
            "biology": "Xaltruvia is classified under the genus {needle}.",
        },
    },
    "C2": {
        "needles": ["Fenvirox", "Vrenzalik", "Qorandel"],
        "questions": {
            "geography": "What is the capital of Xaltruvia?",
            "history": "Which treaty resolved the Xaltruvian conflict?",
            "biology": "In which genus is Xaltruvia classified?",
        },
        "needle_templates": {
            "geography": "The capital of Xaltruvia is {needle}.",
            "history": "The Xaltruvian conflict was resolved by the Treaty of {needle}.",
            "biology": "Xaltruvia is classified under the genus {needle}.",
        },
    },
}
LayoutPosition = Literal["beginning", "middle", "end", "even"]
LayoutGrouping = Literal["sequential", "5pct_apart"]


class NIAHGenerator:
    """Main class for generating NIAH haystacks based on the NeedleConfig and HaystackConfig."""

    def __init__(self, needle_config: NeedleConfig, haystack_config: HaystackConfig):
        self.needle_config = needle_config
        self.haystack_config = haystack_config


    def _compute_insertion_positions(
        self,
        sentences: list[str],
        n_slots: int,
        position: LayoutPosition,
        grouping: LayoutGrouping,
        repetitions: list[int] = None,
    ) -> list[int]:
        """
        Matches the paper's layout strategy:
        - even:       distributed clusters (25%, 50%, 75% for 3 needles)
        - beginning-sequential / middle-sequential / end-sequential:
                cluster of consecutive sentences near that region
        - beginning-5pct_apart / middle-5pct_apart / end-5pct_apart:
                needles separated by 5% of the document length

        Parameters
        ----------
            sentences : list[str]
                The haystack text split into sentences.
            n_slots : int
                The total number of needle insertions (including repetitions).
            position : LayoutPosition
                The general region of the haystack to target for insertions.
            grouping : LayoutGrouping
                How to space out the needles within the haystack.
            repetitions : list[int]
                The count of repetitions for each needle identity.

        Returns
        -------
                list[int] : `n_slots` sentence indices at which to insert needles.

        """
        N = len(sentences)

        if position == "even":
            # For "even", we divide the document based on the number of needle groups.
            # Usually 3 groups (e.g., [5, 5, 5] repetitions).
            reps = repetitions or [1, 1, 1]
            n_groups = len(reps)
            
            # Map each group to an even percentile (e.g. 0.25, 0.50, 0.75 for 3 groups)
            centres = [int(N * (i + 1) / (n_groups + 1)) for i in range(n_groups)]
            
            all_indices = []
            for i, group_reps in enumerate(reps):
                centre = centres[i]
                if grouping == "sequential":
                    # All needles in this group at the same spot
                    all_indices.extend([centre] * group_reps)
                else:  # "5pct_apart"
                    gap = max(1, int(N * 0.05))
                    start = max(0, centre - (group_reps // 2) * gap)
                    group_indices = [min(start + j * gap, N - 1) for j in range(group_reps)]
                    all_indices.extend(group_indices)
            return all_indices

        # Anchor for beginning, middle, end
        region_centres = {"beginning": 0.10, "middle": 0.50, "end": 0.90}
        centre = int(N * region_centres[position])

        if grouping == "sequential":
            # All needles at the same anchor point
            return [centre] * n_slots
        else:  # "5pct_apart"
            gap = max(1, int(N * 0.05))
            start = max(0, centre - (n_slots // 2) * gap)
            return [min(start + i * gap, N - 1) for i in range(n_slots)]


    def build_needle_text(self, needle_name: str, domain: str, needle_set: str) -> str:
        """Return the needle sentence for a given needle name and domain."""
        template = DEFAULT_NEEDLE_SETS[needle_set]["needle_templates"][domain]
        return template.format(needle=needle_name)


    def inject_needles(
        self,
        text: str,
        sentences: list[str],
    ) -> str:
        """
        Inject the three conflicting needles into the haystack.
        
        Parameters
        ----------
            text : str
                The raw haystack text.

        Returns
        -------
            str : 
                The full document string with needles injected.
        """
        random.seed(42)
        
        needle_config = self.needle_config
        haystack_config = self.haystack_config

        ns = DEFAULT_NEEDLE_SETS[haystack_config.needle_set]
        needle_names = ns["needles"]

        # Build the ordered needle list (with repetitions)
        ordered_slots = needle_config.order  # e.g. [0, 1, 2]
        repetitions = needle_config.repetitions  # e.g. [1, 1, 1]

        slot_texts = []
        for slot_idx, (needle_idx, reps) in enumerate(zip(ordered_slots, repetitions)):
            name = needle_names[needle_idx]
            needle_sentence = self.build_needle_text(
                name, haystack_config.question_domain, haystack_config.needle_set
            )
            slot_texts.extend([(slot_idx, name, needle_sentence)] * reps)

        n_insertions = len(slot_texts)

        # Compute insertion indices
        insertion_indices = self._compute_insertion_positions(
            sentences,
            n_insertions,
            haystack_config.position,
            haystack_config.grouping,
            repetitions,
        )

        # Insert needle sentences at computed positions
        result_sentences = list(sentences)
        # Insert in reverse order so earlier indices remain valid (especially for non-sequential)
        for idx, (slot_idx, name, needle_text) in reversed(list(enumerate(slot_texts))):
            ins_pos = insertion_indices[min(idx, len(insertion_indices) - 1)]
            result_sentences.insert(ins_pos, needle_text)

        return " ".join(result_sentences)
