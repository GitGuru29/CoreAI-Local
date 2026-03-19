def build_summary_prompt(text: str, style: str, max_bullets: int | None) -> str:
    style_instructions = {
        "brief": "Keep the summary short and high-signal.",
        "balanced": "Balance brevity with key details.",
        "detailed": "Include the important context, takeaways, and nuance.",
    }
    bullet_instruction = ""
    if max_bullets is not None:
        bullet_instruction = f"Use at most {max_bullets} bullet points or sections.\n"

    return (
        "Summarize the following text.\n"
        f"{style_instructions.get(style, style_instructions['balanced'])}\n"
        f"{bullet_instruction}"
        "Focus on the most important information and keep the wording clear.\n\n"
        "Text to summarize:\n"
        f"{text}"
    )


def build_chat_system_prompt(
    *,
    system_prompt: str | None,
    response_mode: str,
) -> str | None:
    mode_instructions = {
        "guide": (
            "Prefer concise guidance, structured steps, and practical explanation. "
            "Only include code when it materially helps or the user explicitly asks for it."
        ),
        "code": (
            "When the user asks for code, a sample snippet, an implementation, a scaffold, or "
            "asks you to continue with code, provide the code first. Return a concrete runnable "
            "example in fenced code blocks. Do not replace requested code with only high-level "
            "instructions. If assumptions are needed, keep them brief and place them after the code."
        ),
    }

    parts: list[str] = []
    if system_prompt:
        parts.append(system_prompt.strip())
    mode_instruction = mode_instructions.get(response_mode)
    if mode_instruction:
        parts.append(mode_instruction)
    if not parts:
        return None
    return "\n\n".join(parts)


def build_code_analysis_prompt(
    *,
    code: str,
    language: str,
    task: str,
    instructions: str | None,
) -> str:
    task_instructions = {
        "explain": "Explain what the code does and how it is structured.",
        "review": "Review the code for risks, maintainability issues, and edge cases.",
        "find-bugs": "Find likely bugs, logic mistakes, or failure modes.",
        "clean-up": "Suggest a cleaner and more maintainable version of the code.",
        "document": "Write concise documentation and usage notes for the code.",
        "optimize": "Identify performance or simplicity improvements.",
    }
    extra_instructions = ""
    if instructions:
        extra_instructions = f"Additional instruction: {instructions}\n"

    return (
        f"Analyze the following {language} code.\n"
        f"Task: {task_instructions.get(task, task_instructions['explain'])}\n"
        f"{extra_instructions}"
        "Keep the answer practical and specific to the provided code.\n\n"
        "Code:\n"
        f"{code}"
    )
