import React, { useState, useEffect } from 'react';
import type { QuizQuestion } from '../types';
import { VideoOffIcon } from './Icons';

interface QuizProps {
    onComplete: (score: number) => void;
}


const Quiz: React.FC<QuizProps> = ({ onComplete }) => {
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [selectedOption, setSelectedOption] = useState<number | null>(null);
    const [score, setScore] = useState(0);
    const [quizData, setQuizData] = useState<QuizQuestion[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [timeLeft, setTimeLeft] = useState(60);

    // Timer effect
    useEffect(() => {
        if (loading || quizData.length === 0) return;
        
        setTimeLeft(60); // Her yeni soruda 60sn
        
        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    // Süre doldu, otomatik geç
                    handleNext();
                    return 60;
                }
                return prev - 1;
            });
        }, 1000);
        
        return () => clearInterval(timer);
    }, [currentQuestion, loading, quizData.length]);

    useEffect(() => {
        let isMounted = true;
        let hasLoaded = false;
        
        const loadQuiz = async () => {
            if (!isMounted || hasLoaded) return;
            hasLoaded = true;
            
            // Önceden hazırlanmış quiz'i kontrol et
            const preloadedQuiz = localStorage.getItem('preloadedQuiz');
            
            if (preloadedQuiz) {
                try {
                    const questions = JSON.parse(preloadedQuiz);
                    if (isMounted) {
                        setQuizData(questions);
                        setLoading(false);
                    }
                    return;
                } catch (err) {
                    console.error('Preloaded quiz parse hatası:', err);
                }
            }
            
            // Eğer preloaded quiz yoksa, yeni oluştur
            try {
                if (isMounted) setLoading(true);
                
                const response = await fetch('http://localhost:5001/api/agents/quiz', {
                    method: 'POST',
                });
                if (!response.ok) throw new Error('Quiz API request failed');

                const questions = await response.json();
                
                // Quiz'i localStorage'a kaydet
                localStorage.setItem('preloadedQuiz', JSON.stringify(questions));
                
                if (isMounted) {
                    setQuizData(questions);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    setError('Quiz yüklenemedi: ' + err.message);
                    // Fallback quiz
                    setQuizData([
                        {
                            question: "Dijital pazarlama kampanyalarında en önemli metrik hangisidir?",
                            options: ["CTR", "ROI", "Impression", "Reach"],
                            correctAnswerIndex: 1
                        }
                    ]);
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        
        loadQuiz();
        
        return () => {
            isMounted = false;
        };
    }, []);

    const handleNext = async () => {
        if (quizData.length === 0) return;
        
        const isCorrect = selectedOption === quizData[currentQuestion].correctAnswerIndex;

        if (currentQuestion < quizData.length - 1) {
            if (isCorrect) {
                setScore(prevScore => prevScore + 1);
            }
            setSelectedOption(null);
            setCurrentQuestion(prev => prev + 1);
        } else {
            const finalScore = score + (isCorrect ? 1 : 0);
            const quizResults = quizData.map((q, index) => ({
                question: q.question,
                options: q.options,
                selectedAnswer: index === currentQuestion ? selectedOption : -1,
                correctAnswer: q.correctAnswerIndex,
                isCorrect: index === currentQuestion ? isCorrect : false
            }));
            
            // Backend'e quiz sonuçlarını kaydet
            try {
                await fetch('http://localhost:5001/api/save-quiz-results', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sessionId: localStorage.getItem('sessionId') || 'unknown',
                        score: finalScore,
                        totalQuestions: quizData.length,
                        results: quizResults
                    })
                });
            } catch (error) {
                console.error('Quiz sonuçları kaydedilemedi:', error);
            }
            
            onComplete(finalScore);
        }
    };

    if (loading) {
        return (
            <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-gray-200 rounded-2xl shadow-lg flex flex-col justify-center items-center text-gray-500 p-8">
                    <VideoOffIcon className="w-24 h-24 mb-4" />
                    <h3 className="text-2xl font-semibold">Görüşme tamamlandı</h3>
                </div>
                <div className="bg-white rounded-2xl shadow-xl p-8 flex flex-col justify-center items-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#58b0b8]"></div>
                    <p className="mt-4 text-gray-600">Quiz hazırlanıyor...</p>
                </div>
            </div>
        );
    }

    if (error || quizData.length === 0) {
        return (
            <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-gray-200 rounded-2xl shadow-lg flex flex-col justify-center items-center text-gray-500 p-8">
                    <VideoOffIcon className="w-24 h-24 mb-4" />
                    <h3 className="text-2xl font-semibold">Görüşme tamamlandı</h3>
                </div>
                <div className="bg-white rounded-2xl shadow-xl p-8 flex flex-col justify-center items-center">
                    <p className="text-red-600 mb-4">{error}</p>
                    <button 
                        onClick={() => window.location.reload()}
                        className="bg-[#58b0b8] text-white px-4 py-2 rounded-lg"
                    >
                        Sayfayı Yenile
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Placeholder for Video */}
            <div className="lg:col-span-2 bg-gray-200 rounded-2xl shadow-lg flex flex-col justify-center items-center text-gray-500 p-8">
                <VideoOffIcon className="w-24 h-24 mb-4" />
                <h3 className="text-2xl font-semibold">Görüşme tamamlandı</h3>
            </div>

            {/* Quiz Section */}
            <div className="bg-white rounded-2xl shadow-xl p-8 flex flex-col relative">
                {/* Timer - Sağ üst koşe */}
                <div className="absolute top-4 right-4 bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm font-bold">
                    {timeLeft}s
                </div>
                <div className="mb-6">
                    <p className="text-sm font-semibold text-[#58b0b8]">Kişilik Değerlendirmesi - Soru {currentQuestion + 1}/{quizData.length}</p>
                    <h2 className="text-lg font-bold text-gray-800 mt-2">{quizData[currentQuestion]?.question}</h2>
                </div>
                <div className="flex-grow space-y-4">
                    {quizData[currentQuestion]?.options?.map((option, index) => (
                        <label
                            key={index}
                            className={`flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                                selectedOption === index ? 'border-[#58b0b8] bg-teal-50' : 'border-gray-300 bg-white hover:border-[#58b0b8]'
                            }`}
                        >
                            <input
                                type="radio"
                                name="quiz-option"
                                className="h-5 w-5 text-[#58b0b8] focus:ring-[#58b0b8] border-gray-300"
                                checked={selectedOption === index}
                                onChange={() => setSelectedOption(index)}
                            />
                            <span className="ml-4 text-gray-700">{option}</span>
                        </label>
                    ))}
                </div>
                <div className="mt-8 flex items-center gap-4">
                    <button
                        onClick={handleNext}
                        disabled={selectedOption === null}
                        className="w-full bg-[#58b0b8] text-white font-bold py-3 px-4 rounded-lg hover:bg-opacity-90 transition-opacity disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                        {currentQuestion === quizData.length - 1 ? "Tamamla" : "Sonraki"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Quiz;