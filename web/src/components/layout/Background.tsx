"use client";

import { useEffect, useRef } from "react";

export function Background() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let w = canvas.width = window.innerWidth;
        let h = canvas.height = window.innerHeight;

        const resize = () => {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
        };
        window.addEventListener("resize", resize);

        // Orb particles
        const orbs = Array.from({ length: 5 }).map(() => ({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 200 + 100,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            color: Math.random() > 0.5 ? "rgba(99, 102, 241, 0.15)" : "rgba(168, 85, 247, 0.15)" // Indigo vs Purple
        }));

        let animationFrameId: number;

        const animate = () => {
            ctx.fillStyle = "#030712"; // Deep background
            ctx.fillRect(0, 0, w, h);

            orbs.forEach(orb => {
                orb.x += orb.vx;
                orb.y += orb.vy;

                // Bounce
                if (orb.x < -orb.r || orb.x > w + orb.r) orb.vx *= -1;
                if (orb.y < -orb.r || orb.y > h + orb.r) orb.vy *= -1;

                // Draw radial gradient for each orb
                const g = ctx.createRadialGradient(orb.x, orb.y, 0, orb.x, orb.y, orb.r);
                g.addColorStop(0, orb.color);
                g.addColorStop(1, "transparent");

                ctx.fillStyle = g;
                ctx.beginPath();
                ctx.arc(orb.x, orb.y, orb.r, 0, Math.PI * 2);
                ctx.fill();
            });

            // Noise overlay
            // Note: In a real production app, noise is better done with CSS/SVG to save canvas perf, 
            // but simple rect fill here is cheap enough.

            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            window.removeEventListener("resize", resize);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 w-full h-full -z-10 pointer-events-none"
        />
    );
}
