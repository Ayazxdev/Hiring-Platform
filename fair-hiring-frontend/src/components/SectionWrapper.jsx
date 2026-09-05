export default function SectionWrapper({ children, className = '' }) {
    return (
        <section className={`relative w-full min-h-screen bg-bg-dark ${className}`}>
            {children}
        </section>
    );
}
