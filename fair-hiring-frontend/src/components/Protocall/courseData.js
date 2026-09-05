export const COURSE_DATA = {
  'Frontend Engineer': [
    {
      id: 'fe-1',
      title: 'Meta Front-End Developer',
      platform: 'Coursera',
      description: 'Build job-ready skills for an in-demand career as a front-end developer. Learn React, JavaScript, HTML/CSS, and more from Meta engineers.',
      url: 'https://www.coursera.org/professional-certificates/meta-front-end-developer',
      tag: 'Professional Certificate',
    },
    {
      id: 'fe-2',
      title: 'HTML, CSS, and Javascript for Web Developers',
      platform: 'Coursera',
      description: 'Master the essentials of web development: semantic HTML, responsive CSS, and modern JavaScript fundamentals from Johns Hopkins University.',
      url: 'https://www.coursera.org/learn/html-css-javascript-for-web-developers',
      tag: 'Short Course',
    },
    {
      id: 'fe-3',
      title: 'The Complete 2024 Web Development Bootcamp',
      platform: 'Udemy',
      description: 'Become a full-stack web developer with just one course. HTML, CSS, Javascript, Node, React, MongoDB, Web3 and DApps.',
      url: 'https://www.udemy.com/course/the-complete-web-development-bootcamp/',
      tag: 'Bestseller',
    },
    {
      id: 'fe-4',
      title: 'React - The Complete Guide (incl. React Router & Redux)',
      platform: 'Udemy',
      description: 'Dive in and learn React.js from scratch! Learn React, Hooks, Redux, React Router, Next.js, Best Practices and way more.',
      url: 'https://www.udemy.com/course/react-the-complete-guide-incl-redux/',
      tag: 'Bestseller',
    },
  ],
  'Backend Engineer': [
    {
      id: 'be-1',
      title: 'Meta Back-End Developer',
      platform: 'Coursera',
      description: 'Launch your career as a back-end developer. Build the skills you need to work with APIs, databases, and server-side development from Meta.',
      url: 'https://www.coursera.org/professional-certificates/meta-back-end-developer',
      tag: 'Professional Certificate',
    },
    {
      id: 'be-2',
      title: 'Server-side JavaScript with Node.js',
      platform: 'Coursera',
      description: 'Develop server-side web applications with Node.js. Learn Express.js, REST APIs, and backend architecture patterns from NIIT.',
      url: 'https://www.coursera.org/learn/server-side-javascript',
      tag: 'Short Course',
    },
    {
      id: 'be-3',
      title: 'NodeJS - The Complete Guide (MVC, REST APIs, GraphQL)',
      platform: 'Udemy',
      description: 'Master Node.js by building a real-world application with Node.js, Express.js, MongoDB, Mongoose, and REST APIs.',
      url: 'https://www.udemy.com/course/nodejs-the-complete-guide/',
      tag: 'Bestseller',
    },
    {
      id: 'be-4',
      title: 'Docker & Kubernetes: The Practical Guide',
      platform: 'Udemy',
      description: 'Learn Docker, Docker Compose, Multi-Container Projects, Deployment and all about Kubernetes from the ground up.',
      url: 'https://www.udemy.com/course/docker-kubernetes-the-practical-guide/',
      tag: 'Highest Rated',
    },
  ],
  'AI Engineer': [
    {
      id: 'ai-1',
      title: 'Machine Learning Specialization',
      platform: 'Coursera',
      description: 'Build ML models with NumPy & scikit-learn, build & train neural networks with TensorFlow. Taught by Andrew Ng from Stanford/DeepLearning.AI.',
      url: 'https://www.coursera.org/specializations/machine-learning-introduction',
      tag: 'Specialization',
    },
    {
      id: 'ai-2',
      title: 'Deep Learning Specialization',
      platform: 'Coursera',
      description: 'Become a Deep Learning expert. Master neural networks, CNNs, RNNs, transformers and more with DeepLearning.AI.',
      url: 'https://www.coursera.org/specializations/deep-learning',
      tag: 'Specialization',
    },
    {
      id: 'ai-3',
      title: 'Complete A.I. & Machine Learning, Data Science Bootcamp',
      platform: 'Udemy',
      description: 'Become an AI, machine learning and data science expert. Use Python, TensorFlow, and pandas to build production-grade ML systems.',
      url: 'https://www.udemy.com/course/complete-machine-learning-and-data-science-zero-to-mastery/',
      tag: 'Bestseller',
    },
    {
      id: 'ai-4',
      title: 'PyTorch for Deep Learning Bootcamp',
      platform: 'Udemy',
      description: 'Learn PyTorch for deep learning covering everything from the basics to advanced topics like computer vision and NLP.',
      url: 'https://www.udemy.com/course/pytorch-for-deep-learning-and-computer-vision/',
      tag: 'Highest Rated',
    },
  ],
  'ML Ops': [
    {
      id: 'mlo-1',
      title: 'MLOps | Machine Learning Operations Specialization',
      platform: 'Coursera',
      description: 'Implement MLOps practices from Duke University. Covers CI/CD for ML, model deployment, monitoring, and automation pipelines.',
      url: 'https://www.coursera.org/specializations/mlops-machine-learning-duke',
      tag: 'Specialization',
    },
    {
      id: 'mlo-2',
      title: 'Machine Learning Engineering for Production (MLOps)',
      platform: 'Coursera',
      description: 'Deploy ML models and build MLOps pipelines. Learn to manage the full ML lifecycle in production with DeepLearning.AI.',
      url: 'https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops',
      tag: 'Specialization',
    },
    {
      id: 'mlo-3',
      title: 'MLOps Bootcamp: Mastering AI Operations for Success',
      platform: 'Udemy',
      description: 'Complete MLOps guide covering model versioning with MLflow, pipeline automation with Airflow, and deployment with Kubernetes.',
      url: 'https://www.udemy.com/course/mlops-course/',
      tag: 'New & Trending',
    },
    {
      id: 'mlo-4',
      title: 'Kubernetes for Machine Learning',
      platform: 'Udemy',
      description: 'Learn to orchestrate ML workloads with Kubernetes. Deploy, scale, and manage ML models in production Kubernetes clusters.',
      url: 'https://www.udemy.com/course/kubernetes-for-machine-learning/',
      tag: 'Short Course',
    },
  ],
};

export const SUPPORTED_ROLES = Object.keys(COURSE_DATA);

const ROLE_ALIASES = {
  'Frontend Engineer': ['frontend', 'fe', 'ui developer', 'web developer', 'react'],
  'Backend Engineer': ['backend', 'be', 'server', 'node', 'api'],
  'AI Engineer': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'data science', 'deep learning'],
  'ML Ops': ['mlops', 'ml','ml operations', 'machine learning ops', 'model ops']
};

export function getCoursesForRole(roleQuery) {
  if (!roleQuery) return null;
  
  const query = roleQuery.toLowerCase().trim();
  
  // 1. Check for exact match in keys
  const exactMatch = SUPPORTED_ROLES.find(role => role.toLowerCase() === query);
  if (exactMatch) return COURSE_DATA[exactMatch];

  // 2. Check for alias match
  for (const [role, aliases] of Object.entries(ROLE_ALIASES)) {
    if (aliases.some(alias => alias.toLowerCase() === query)) {
      return COURSE_DATA[role];
    }
  }

  // 3. Check for substring match in keys or aliases
  const matchedRoles = new Set();
  
  const queryRegex = new RegExp(`\\b${query}\\b`, 'i');

  SUPPORTED_ROLES.forEach(role => {
    const roleLower = role.toLowerCase();
    if (queryRegex.test(roleLower) || (query.length >= 3 && roleLower.includes(query)) || query.includes(roleLower)) {
      matchedRoles.add(role);
    }
  });

  Object.entries(ROLE_ALIASES).forEach(([role, aliases]) => {
    if (aliases.some(alias => {
      const aliasLower = alias.toLowerCase();
      return queryRegex.test(aliasLower) || (query.length >= 3 && aliasLower.includes(query)) || query.includes(aliasLower);
    })) {
      matchedRoles.add(role);
    }
  });

  if (matchedRoles.size > 0) {
    // Merge courses from all matched roles, avoiding duplicates if any (though IDs are unique)
    const allCourses = [];
    const seenIds = new Set();
    
    matchedRoles.forEach(role => {
      COURSE_DATA[role].forEach(course => {
        if (!seenIds.has(course.id)) {
          allCourses.push(course);
          seenIds.add(course.id);
        }
      });
    });
    
    return allCourses;
  }

  return null;
}
