import { useEffect, useRef } from 'react';

export default function VisionVideo() {
    const videoRef = useRef(null);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        // Use Intersection Observer to play only when visible
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        video.play().catch((error) => {
                            console.log("Video autoplay prevented:", error.message);
                        });
                    } else {
                        video.pause();
                    }
                });
            },
            { threshold: 0.5 }
        );

        observer.observe(video);
        return () => observer.disconnect();
    }, []);

    return (
        <div className="relative w-full rounded-lg overflow-hidden shadow-xl">
            <video
                ref={videoRef}
                className="w-full h-auto"
                loop
                muted
                playsInline
                preload="auto"
                src="/media/video/2nd%20sec.mp4"
            >
                Your browser does not support the video tag.
            </video>
        </div>
    );
}
