import React from 'react';
import { getCoursesForRole } from './courseData';

const PLATFORM_COLORS = {
  Coursera: { bg: '#407E86', text: '#ffffff' },
  Udemy: { bg: '#A58D66', text: '#ffffff' },
};

function ExternalLinkIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="square"
      strokeLinejoin="miter"
    >
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

export function CourseRecommendations({ role }) {
  const courses = getCoursesForRole(role);

  if (!courses) return null;

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between border-b-[3px] border-[#1c1c1c] pb-8">
        <div className="space-y-2">
          <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#1c1c1c]/40 font-grotesk">
            Recommended Learning Path
          </span>
          <h3 className="text-3xl font-black text-[#1c1c1c] uppercase font-montreal tracking-tight">
            Curated Courses
          </h3>
        </div>
        <div className="px-5 py-2 border-[2px] border-[#1c1c1c] text-[9px] font-black uppercase font-grotesk">
          For: {role}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {courses.map((course) => {
          const platformStyle = PLATFORM_COLORS[course.platform] || { bg: '#1c1c1c', text: '#ffffff' };
          return (
            <div
              key={course.id}
              className="bg-white border-[3px] border-[#1c1c1c] p-8 shadow-[8px_8px_0px_rgba(28,28,28,0.1)] flex flex-col gap-4 hover:-translate-y-1 hover:shadow-[12px_12px_0px_rgba(28,28,28,0.15)] transition-all duration-200"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 flex-wrap">
                  <span
                    className="text-[9px] font-black uppercase tracking-[0.2em] px-3 py-1 font-grotesk"
                    style={{ backgroundColor: platformStyle.bg, color: platformStyle.text }}
                  >
                    {course.platform}
                  </span>
                  <span className="text-[9px] font-black uppercase tracking-[0.2em] border-[2px] border-[#1c1c1c] px-3 py-1 text-[#1c1c1c] font-grotesk">
                    {course.tag}
                  </span>
                </div>
                <a
                  href={course.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 w-10 h-10 flex items-center justify-center border-[2px] border-[#1c1c1c] text-[#1c1c1c] hover:bg-[#1c1c1c] hover:text-white transition-colors"
                  aria-label={`Open ${course.title}`}
                >
                  <ExternalLinkIcon />
                </a>
              </div>

              <h4 className="text-base font-black text-[#1c1c1c] uppercase font-montreal leading-tight">
                {course.title}
              </h4>

              <p className="text-[11px] font-black text-[#1c1c1c]/60 font-grotesk uppercase leading-relaxed tracking-wide flex-1">
                {course.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
