"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Background } from "@/components/layout/Background";
import { OptionButton } from "@/components/ui/OptionButton";
import { ProgressBar } from "@/components/ui/ProgressBar";

// --- Types ---
declare global {
  interface Window {
    Telegram: {
      WebApp: any;
    };
  }
}

interface Question {
  question_text: string;
  type: "multiple_choice" | "open_text";
  variants?: string[];
}

interface Result {
  question: string;
  answer: string;
}

export default function SurveyPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  useEffect(() => {
    // Initialize Telegram WebApp Styling
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.expand();
      tg.ready();
      tg.setHeaderColor("#030712"); // Matches new bg
      tg.setBackgroundColor("#030712");
    }

    // Load Data
    try {
      const hash = window.location.hash.substring(1);
      if (!hash) {
        // Fallback demo data
        setQuestions([{
          question_text: "Какой стиль интерфейса вам нравится?",
          type: "multiple_choice",
          variants: ["Минимализм", "Глассморфизм", "Нео-брутализм", "Киберпанк"]
        }, {
          question_text: "Как часто вы используете Telegram Apps?",
          type: "multiple_choice",
          variants: ["Ежедневно", "Иногда", "Редко", "Впервые вижу"]
        }]);
        setLoading(false);
        return;
      }

      let jsonStr = "";
      const cleanHash = hash.split(/[?&]/)[0];

      if (cleanHash.startsWith("d=")) {
        const b64 = cleanHash.substring(2);
        const binary = atob(b64.replace(/-/g, "+").replace(/_/g, "/"));
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        jsonStr = new TextDecoder().decode(bytes);
      } else {
        jsonStr = decodeURIComponent(cleanHash);
      }

      if (jsonStr) {
        const parsed = JSON.parse(jsonStr);
        setQuestions(parsed);
      }
    } catch (e) {
      console.error("Parse error:", e);
      setQuestions([{
        question_text: "Ошибка загрузки данных",
        type: "multiple_choice",
        variants: ["Перезагрузить"]
      }]);
    }
    setLoading(false);
  }, []);

  const handleFinish = useCallback((finalAnswers: string[]) => {
    const tg = window.Telegram?.WebApp;
    const result: Result[] = questions.map((q, i) => ({
      question: q.question_text,
      answer: finalAnswers[i],
    }));

    if (tg) {
      tg.sendData(JSON.stringify(result));
      tg.close();
    } else {
      console.log("Finished! Results:", result);
    }
  }, [questions]);

  const handleOptionSelect = (option: string) => {
    if (selectedOption) return;
    setSelectedOption(option);

    setTimeout(() => awaitNextStep(option), 500); // 500ms delay to view selection
  };

  const awaitNextStep = (option: string) => {
    const updatedAnswers = [...answers];
    updatedAnswers[currentStep] = option;
    setAnswers(updatedAnswers);

    if (currentStep < questions.length - 1) {
      setCurrentStep((prev) => prev + 1);
      setSelectedOption(null);
    } else {
      handleFinish(updatedAnswers);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center text-indigo-400 font-medium tracking-widest bg-[#030712]">
        <div className="flex gap-2">
          <span className="animate-bounce delay-0">●</span>
          <span className="animate-bounce delay-150">●</span>
          <span className="animate-bounce delay-300">●</span>
        </div>
      </main>
    );
  }

  const q = questions[currentStep];
  const variants = q.variants && q.variants.length > 0 ? q.variants : ["Да", "Нет"];

  return (
    <>
      <Background />
      {/* 
        Mobile Layout Optimization: 
        - h-[100dvh] ensures it takes full viewport height on mobile, preventing default scroll.
        - Flex layout handles the distribution of space.
      */}
      <main className="h-[100dvh] w-full flex flex-col p-4 md:p-8 relative overflow-hidden supports-[height:100dvh]:h-[100dvh]">

        {/* Header Area */}
        <div className="w-full max-w-lg mx-auto flex-none pt-4 pb-2">
          {/* Removed 'Question X' text as requested */}
          <ProgressBar current={currentStep} total={questions.length} />
        </div>

        {/* Content Area - Flex Grow to Center */}
        <div className="flex-1 w-full max-w-lg mx-auto flex flex-col justify-center min-h-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, y: 20, filter: "blur(5px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, y: -20, filter: "blur(5px)" }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="w-full flex flex-col gap-5 md:gap-8 max-h-full"
            >
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-center text-white drop-shadow-2xl leading-tight py-2">
                {q.question_text}
              </h1>

              <div className="grid gap-3 overflow-y-auto pr-1 pb-1 scrollbar-hide -mr-1">
                {variants.map((variant, idx) => (
                  <OptionButton
                    key={idx}
                    index={idx}
                    label={variant}
                    selected={selectedOption === variant}
                    disabled={selectedOption !== null}
                    onClick={() => handleOptionSelect(variant)}
                  />
                ))}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Bottom Spacer/Footer area to prevent bottom cutoff on some devices */}
        <div className="h-4 md:h-8 flex-none" />
      </main>
    </>
  );
}
