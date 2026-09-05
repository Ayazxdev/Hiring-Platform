export default function GridPlus({ className = "" }) {
    return (
        <span className={`absolute z-50 pointer-events-none select-none font-grotesk text-[14px] md:text-[16px] text-[#1c1c1c] opacity-20 transform -translate-x-1/2 -translate-y-1/2 ${className}`}>
            +
        </span>
    );
}
