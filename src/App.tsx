import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type { Page } from './types';
import Scheduling from './components/Scheduling';
import Chatbot from './components/Chatbot';
import Quiz from './components/Quiz';
import QnA from './components/QnA';
import WaitingRoom from './components/WaitingRoom';
import Interview from './components/Interview';
import Completion from './components/Completion';

// This is a mock user avatar, in a real app this would be dynamic
const UserAvatar: React.FC = () => (
    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#58b0b8] to-[#4a9ca4] flex items-center justify-center">
        <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
    </div>
);

const App: React.FC = () => {
    const [page, setPage] = useState<Page>('scheduling');
    // Dinamik session ID: jobId-candidateId formatı
    // URL'den sessionId al, yoksa default kullan
    const getSessionIdFromUrl = () => {
        const params = new URLSearchParams(window.location.search);
        const sessionId = params.get('sessionId') || 'Genar-00001-00001';
        console.log('🔍 URL sessionId:', sessionId);
        return sessionId;
    };
    const sessionIdRef = useRef<string>(getSessionIdFromUrl());
    const [isLoaded, setIsLoaded] = useState(false);
    const [quizScore, setQuizScore] = useState(0);
    const [isQuizDone, setIsQuizDone] = useState(false);
    const [quizPreloaded, setQuizPreloaded] = useState(false);

    useEffect(() => {
        // Prevent flash of content before styles are loaded, especially with CDN
        const timer = setTimeout(() => setIsLoaded(true), 100);
        return () => clearTimeout(timer);
    }, []);
    
    useEffect(() => {
        // 5 dakika kala quiz'i önceden oluştur
        if (page !== 'waiting' || quizPreloaded) return;
        
        const checkAndPreloadQuiz = () => {
            const scheduled = localStorage.getItem('scheduledInterview');
            if (!scheduled) return;
            
            const data = JSON.parse(scheduled);
            const scheduledDateTime = new Date(data.scheduledDateTime);
            const now = new Date();
            const timeUntilInterview = scheduledDateTime.getTime() - now.getTime();
            
            // 5 dakika kala quiz'i oluştur
            if (timeUntilInterview <= 300000 && timeUntilInterview > 0 && !quizPreloaded) {
                console.log('🟢 5 dakika kaldı, quiz oluşturuluyor...');
                fetch('http://localhost:5001/api/agents/quiz', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('✅ Quiz önceden oluşturuldu:', data);
                    localStorage.setItem('preloadedQuiz', JSON.stringify(data));
                    setQuizPreloaded(true);
                })
                .catch(error => console.error('❌ Quiz oluşturma hatası:', error));
            }
        };
        
        // Her saniye kontrol et
        const interval = setInterval(checkAndPreloadQuiz, 1000);
        checkAndPreloadQuiz(); // Hemen bir kez çalıştır
        
        return () => clearInterval(interval);
    }, [page, quizPreloaded]);

    const handleQuizComplete = (score: number) => {
        setQuizScore(score);
        setIsQuizDone(true);
        setPage('qna');
    };

    const handleRestart = () => {
        setQuizScore(0);
        setIsQuizDone(false);
        // Mülakat yeniden başladığında eski verileri temizle
        localStorage.removeItem('preInterviewChat');
        localStorage.removeItem('quizResults');
        // Yeni session ID oluştur (farklı aday için)
        const currentId = sessionIdRef.current.split('-');
        const newCandidateId = String(parseInt(currentId[2]) + 1).padStart(5, '0');
        sessionIdRef.current = `${currentId[0]}-${currentId[1]}-${newCandidateId}`;
        console.log(`🆕 Yeni session ID: ${sessionIdRef.current}`);
        // URL'yi de güncelle
        window.history.replaceState({}, '', `?sessionId=${sessionIdRef.current}`);
        setPage('scheduling');
    };

    const renderPage = () => {
        switch (page) {
            case 'scheduling':
                return <Scheduling onStart={() => setPage('chatbot')} onScheduleLater={() => setPage('waiting')} />;
            case 'waiting':
                return <WaitingRoom onCountdownFinish={() => setPage('chatbot')} />;
            case 'chatbot':
                // Mülakat öncesi sohbetten sonra doğrudan quiz'e geçiş yapılıyor.
                return <Chatbot sessionId={sessionIdRef.current} mode="pre-interview" onStartInterview={() => setPage('interview')} onStartQuiz={() => setPage('quiz')} />;
            case 'interview':
                return <Interview sessionId={sessionIdRef.current} onStartQuiz={() => setPage('quiz')} />;
            case 'quiz':
                return <Quiz onComplete={handleQuizComplete} />;
            case 'qna':
                return <QnA sessionId={sessionIdRef.current} onComplete={() => setPage('completion')} />;
            case 'completion':
                return <Completion score={quizScore} totalQuestions={10} sessionId={sessionIdRef.current} onRestart={handleRestart} />;
            default:
                return <Scheduling onStart={() => setPage('chatbot')} onScheduleLater={() => setPage('waiting')} />;
        }
    };

    if (!isLoaded) {
        return <div className="w-screen h-screen bg-gray-50"></div>;
    }
    
    const getHeaderText = () => {
        switch (page) {
            case 'qna':
                return 'Soru & Cevap';
            case 'completion':
                return 'Mülakat Tamamlandı';
            default:
                return 'Video Mülakat Platformu';
        }
    }


    return (
        <div className="min-h-screen bg-gray-100 font-sans flex flex-col">
            <header className="bg-white shadow-sm w-full">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <h1 className="text-xl font-semibold text-gray-800">
                           {getHeaderText()}
                        </h1>
                        <UserAvatar />
                    </div>
                </div>
            </header>
            <main className="flex-grow flex items-center justify-center p-4 sm:p-6 lg:p-8">
                {renderPage()}
            </main>
        </div>
    );
};

export default App;