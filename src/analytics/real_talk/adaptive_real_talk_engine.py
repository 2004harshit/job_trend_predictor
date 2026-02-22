class AdaptiveRealTalkEngine:
    def __init__(self):
        pass

    def get_domain_persona(self, metrics):
        # Classify the domain based on metrics
        if metrics['barrier_depth'] >= 2 and metrics['competition'] > 7:
            return "THE_GAUNTLET"  # e.g., ML, Data Science, Quant
        elif metrics['competition'] > 8 and metrics['barrier_depth'] <= 1:
            return "THE_CROWDED_ROOM" # e.g., Frontend, UI/UX, Manual QA
        elif metrics['growth'] > 0.5 and metrics['stability'] < 0.5:
            return "THE_GOLD_RUSH" # e.g., Blockchain, Prompt Engineering
        else:
            return "THE_STEADY_CLIMB" # e.g., Backend Java, DevOps, SQL Dev

    def generate_real_talk(self, domain, metrics):
        persona = self.get_domain_persona(metrics)
        
        # Dictionary of logic-based templates
        templates = {
            "THE_GAUNTLET": {
                "Truth": f"Interviews are essentially 'Math exams' in disguise. If you can't explain the logic behind the library, you're out.",
                "Trap": "Spending months on coding syntax while ignoring the underlying Statistics.",
                "Pattern": "Candidates with research papers or math-heavy GitHub repos bypass the filter."
            },
            "THE_CROWDED_ROOM": {
                "Truth": "1,000+ people apply for every role. Your resume has 6 seconds to impress an exhausted recruiter.",
                "Trap": "Building the same 'Portfolio Project' as everyone else (e.g., Netflix clones).",
                "Pattern": "Referrals and niche specializations (e.g., WebGL, Accessibility) are the only way to skip the line."
            },
            "THE_GOLD_RUSH": {
                "Truth": "Demand is high, but the tech changes every 3 months. What you learn today might be obsolete by next year.",
                "Trap": "Chasing high salaries without building foundational engineering skills.",
                "Pattern": "The winners are 'Early Adopters' who ship open-source tools for the new tech first."
            },
            "THE_STEADY_CLIMB": {
                "Truth": "It’s not flashy, but it’s the backbone of tech. Reliability matters more than 'innovation' here.",
                "Trap": "Thinking you're 'safe' and stopping your learning after getting the job.",
                "Pattern": "Certifications in Cloud (AWS/Azure) and System Design knowledge double your market value."
            }
        }

        # Select the specific template
        t = templates[persona]

        return {
            "Persona": persona,
            "🔴 Harsh Truth": t["Truth"],
            "🟢 Silver Lining": f"High rewards for those who survive the {persona.replace('_', ' ').lower()} phase.",
            "⚠️ Beginner Trap": t["Trap"],
            "✅ Success Pattern": t["Pattern"]
        }
    


if __name__ == "__main__":    # Example usage
    metrics_example = {
        'barrier_depth': 3,
        'competition': 8,
        'growth': 0.4,
        'stability': 0.3
    }
    engine = AdaptiveRealTalkEngine()
    report = engine.generate_real_talk("Data Scientist", metrics_example)
    print(report)