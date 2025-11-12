import React, { useState, useEffect, useRef } from 'react';

interface ChatMessage {
    sender: 'user' | 'assistant';
    text: string;
}

interface QnAProps {
    sessionId: string;
    onComplete: () => void;
}

const AssistantAvatar: React.FC = () => (
    <div className="w-12 h-12 rounded-full bg-white flex-shrink-0 flex items-center justify-center overflow-hidden border-2 border-gray-200">
        <img src="/assets/logo.png" alt="Company Logo" className="w-full h-full object-cover" />
    </div>
);

const UserAvatar: React.FC = () => (
    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#58b0b8] to-[#4a9ca4] flex-shrink-0 flex items-center justify-center">
        <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
    </div>
);

const SendIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
    </svg>
);

const QnA: React.FC<QnAProps> = ({ sessionId, onComplete }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isRecording, setIsRecording] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const initializedRef = useRef(false); // React Strict Mode için
    
    const handlePlayAudio = (text: string) => {
        if (isSpeaking || !text?.trim()) return;
        setIsSpeaking(true);
        const cleanText = text.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'tr-TR';
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
    };

    const startRecording = () => {
        if (isRecording || !('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;
        
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'tr-TR';
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onstart = () => setIsRecording(true);
        recognition.onend = () => {
            if (isRecording) {
                setIsRecording(false);
            }
        };
        recognition.onresult = (event: any) => {
            let transcript = '';
            for (let i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            setInputValue(transcript);
        };
        recognition.onerror = () => setIsRecording(false);

        mediaRecorderRef.current = recognition;
        recognition.start();
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            (mediaRecorderRef.current as any).stop();
            setIsRecording(false);
        }
    };
    
    const handleMicrophoneClick = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    useEffect(() => {
        if (initializedRef.current) return;
        initializedRef.current = true;
        
        const initializeEndingAgent = async () => {
            try {
                // Ending agent'ı başlat
                console.log('🔴 QnA: QUIZ_COMPLETED sinyali gönderiliyor...');
                const response = await fetch('http://localhost:5001/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sessionId: sessionId,
                        userMessage: 'QUIZ_COMPLETED'
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log('🔴 QnA: Backend data:', data);
                    console.log('🔴 QnA: Conversation history length:', data.conversation_history?.length);
                    console.log('🔴 QnA: Response text:', data.response);
                    
                    if (data.conversation_history && data.conversation_history.length > 0) {
                        setMessages(data.conversation_history);
                        console.log('🔴 QnA: Conversation history güncellendi:', data.conversation_history);
                    } else if (data.response) {
                        // Eğer history boşsa ama response varsa, sadece response'u ekle
                        setMessages([{ sender: 'assistant', text: data.response }]);
                        console.log('🔴 QnA: Sadece response eklendi');
                    }
                }
            } catch (error) {
                console.error('Ending agent başlatma hatası:', error);
                setMessages(prev => [...prev, { 
                    sender: 'assistant', 
                    text: 'Tebrikler, mülakatın temel aşamalarını tamamladınız! Şimdi pozisyon, şirket veya süreç hakkında sorularınız varsa yanıtlamaktan memnuniyet duyarım.' 
                }]);
            } finally {
                setIsLoading(false);
            }
        };

        initializeEndingAgent();
    }, []);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTo({ 
                top: chatContainerRef.current.scrollHeight, 
                behavior: 'smooth' 
            });
        }
    }, [messages]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage: ChatMessage = { sender: 'user', text: inputValue };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);
        
        try {
            const response = await fetch('http://localhost:5001/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sessionId: sessionId,
                    userMessage: userMessage.text,
                }),
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.response) {
                    const agentMessage: ChatMessage = { sender: 'assistant', text: data.response };
                    setMessages(prev => [...prev, agentMessage]);
                }

                if (data.action === 'FINISH_INTERVIEW') {
                    setTimeout(() => onComplete(), 2000);
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, { 
                sender: 'assistant', 
                text: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.' 
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full max-w-4xl h-[75vh] bg-white rounded-2xl shadow-xl flex flex-col">
            <div className="p-4 border-b flex items-center">
                <AssistantAvatar />
                <div className="ml-4">
                    <h2 className="font-semibold text-gray-800">İşe Alım Uzmanı</h2>
                    <p className="text-sm text-green-500">Online</p>
                </div>
            </div>
            
            <div ref={chatContainerRef} className="flex-1 p-6 space-y-6 overflow-y-auto">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex items-start gap-4 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                        {msg.sender === 'assistant' && <AssistantAvatar />}
                        <div className={`rounded-2xl p-4 max-w-lg ${msg.sender === 'user' ? 'bg-[#58b0b8] text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'}`}>
                            <p className="whitespace-pre-wrap">{msg.text}</p>
                            {msg.sender === 'assistant' && (
                                <button 
                                    onClick={() => handlePlayAudio(msg.text)} 
                                    className={`mt-2 text-gray-500 hover:text-gray-800 disabled:text-gray-300 ${isSpeaking ? 'text-green-500' : ''}`}
                                    disabled={isSpeaking}
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"/>
                                    </svg>
                                </button>
                            )}
                        </div>
                        {msg.sender === 'user' && <UserAvatar />}
                    </div>
                ))}
                
                {isLoading && (
                    <div className="flex items-start gap-4">
                        <AssistantAvatar />
                        <div className="rounded-2xl p-4 bg-gray-100">
                            <div className="flex gap-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            
            <div className="p-4 border-t bg-gray-50 rounded-b-2xl">
                <div className="flex items-center bg-white border border-gray-300 rounded-lg px-2 py-1">
                    <UserAvatar />
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder={isRecording ? "Dinliyorum..." : "Sorunuzu yazın veya mikrofona tıklayın..."}
                        className="flex-1 px-4 py-2 bg-transparent focus:outline-none"
                        disabled={isLoading}
                    />
                    <button 
                        onClick={handleMicrophoneClick} 
                        className={`p-2 text-gray-500 hover:text-[#58b0b8] ${isRecording ? 'text-red-500 animate-pulse' : ''}`}
                        disabled={isLoading}
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                        </svg>
                    </button>
                    <button 
                        onClick={handleSend} 
                        disabled={isLoading || !inputValue.trim()} 
                        className="p-2 text-white bg-[#58b0b8] rounded-lg ml-2 hover:bg-opacity-90 disabled:bg-gray-400"
                    >
                        <SendIcon className="w-6 h-6" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default QnA;