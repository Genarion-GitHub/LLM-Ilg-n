import React, { useEffect, useRef, useState } from 'react';
import { MicrophoneIcon, MicOffIcon, VideoOnIcon, VideoOffIcon, EndCallIcon, MoreIcon, LightbulbIcon, CheckCircleIcon, BriefcaseIcon, SpeakerphoneIcon } from './Icons';

interface InterviewProps {
    onStartQuiz: () => void;
    sessionId: string;
}

const Interview: React.FC<InterviewProps> = ({ onStartQuiz, sessionId }) => {
    const userVideoRef = useRef<HTMLVideoElement>(null);
    const [error, setError] = useState<string | null>(null);
    const [isMicOn, setIsMicOn] = useState(true);
    const [isVideoOn, setIsVideoOn] = useState(true);

    useEffect(() => {
        // Interview agent'ı başlat ve otomatik quiz geçişini kontrol et
        const startInterview = async () => {
            try {
                const response = await fetch('http://localhost:5001/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sessionId: sessionId,
                        userMessage: 'INTERVIEW_STARTED'
                    })
                });
                const data = await response.json();
                console.log('🎥 Interview response:', data);
                
                // Eğer SHOW_QUIZ action'ı varsa quiz'e geç
                if (data.action === 'SHOW_QUIZ' || data.action === 'START_QUIZ') {
                    console.log('✅ Auto-starting quiz from interview');
                    setTimeout(() => {
                        onStartQuiz();
                    }, 2000); // 2 saniye bekle
                }
            } catch (error) {
                console.error('Interview başlatma hatası:', error);
            }
        };
        
        startInterview();
    }, [sessionId]);

    const interviewTips = [
        { Icon: LightbulbIcon, text: 'Sessiz ve iyi aydınlatılmış bir ortam seçin. Arka planınızın düzenli ve profesyonel olmasına özen gösterin.' },
        { Icon: CheckCircleIcon, text: 'Görüşmeden önce internet bağlantınızı, kamera ve mikrofonunuzu test edin. Teknik sorunları en aza indirin.' },
        { Icon: BriefcaseIcon, text: 'Profesyonel bir kıyafet seçin. Yüz yüze bir görüşmeye gider gibi giyinmek, doğru izlenimi bırakmanıza yardımcı olur.' },
        { Icon: SpeakerphoneIcon, text: 'Net ve anlaşılır bir şekilde konuşun. Kameraya bakarak göz teması kurmaya çalışın.' },
        { Icon: CheckCircleIcon, text: 'Görüşme sonunda bir quiz bölümü olacaktır. Dikkatle dinleyin ve kendinize güvenin. Başarılar!' }
    ];

    return (
        <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Video Section */}
            <div className="lg:col-span-2 bg-black rounded-2xl shadow-xl overflow-hidden relative flex flex-col justify-center items-center">
                <div className="w-full h-full bg-gradient-to-br from-[#58b0b8] to-[#4a9ca4] flex items-center justify-center">
                    <img src="/assets/logo.png" alt="Company Logo" className="w-full h-full object-cover" />
                </div>
                <div className="absolute top-4 right-4 w-40 h-32 rounded-lg overflow-hidden border-2 border-white shadow-lg">
                    <div className="w-full h-full bg-gray-800 text-white flex items-center justify-center p-2 text-center text-xs">
                        <p>Kamera kapalı</p>
                    </div>
                    <div className="absolute bottom-0 left-0 bg-black bg-opacity-50 text-white px-2 py-1 text-sm font-semibold">
                        Aday
                    </div>
                </div>
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2">
                    <div className="flex items-center gap-4 bg-white/10 backdrop-blur-sm p-3 rounded-full">
                        <button onClick={() => setIsMicOn(!isMicOn)} className={`w-12 h-12 rounded-full flex items-center justify-center text-white transition-colors ${isMicOn ? 'bg-white/20 hover:bg-white/30' : 'bg-red-600 hover:bg-red-700'}`}>
                            {isMicOn ? <MicrophoneIcon className="w-6 h-6" /> : <MicOffIcon className="w-6 h-6" />}
                        </button>
                        <button onClick={() => setIsVideoOn(!isVideoOn)} className={`w-12 h-12 rounded-full flex items-center justify-center text-white transition-colors ${isVideoOn ? 'bg-white/20 hover:bg-white/30' : 'bg-red-600 hover:bg-red-700'}`}>
                            {isVideoOn ? <VideoOnIcon className="w-6 h-6" /> : <VideoOffIcon className="w-6 h-6" />}
                        </button>
                        <button
                            onClick={onStartQuiz}
                            className="w-14 h-14 bg-red-600 rounded-full flex items-center justify-center text-white hover:bg-red-700 transition-colors"
                        >
                            <EndCallIcon className="w-7 h-7" />
                        </button>
                        <button className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-white hover:bg-white/30 transition-colors">
                            <MoreIcon className="w-6 h-6" />
                        </button>
                    </div>
                </div>
                <div className="absolute top-4 left-4 bg-black bg-opacity-50 text-white px-3 py-1.5 rounded-lg text-lg font-semibold">
                    Genarion AI
                </div>
            </div>

            {/* Info and Action Section */}
            <div className="bg-white rounded-2xl shadow-xl p-6 flex flex-col">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Mülakatta Dikkat Edilmesi Gerekenler</h2>
                <div className="space-y-4 text-gray-600">
                    {interviewTips.map((tip, index) => (
                        <div key={index} className="flex items-start gap-3">
                            <tip.Icon className="w-6 h-6 text-[#58b0b8] flex-shrink-0 mt-1" />
                            <p className="text-sm">{tip.text}</p>
                        </div>
                    ))}
                </div>
                <div className="mt-auto p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800 text-center">
                        💡 Mülakat tamamlandığında otomatik olarak quiz'e yönlendirileceksiniz
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Interview;