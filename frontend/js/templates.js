/**
 * DecisionDeck - Decision Templates
 * Curated templates for common decision scenarios.
 * All numbers and weights are illustrative and fully customizable by the user.
 */

const DECISION_TEMPLATES = [
  {
    id: 'career',
    title: 'Career Path Comparison',
    badge: 'Career',
    description: 'Compare potential career directions based on market demand, personal passion, and learning curve.',
    options: [
      { id: 'opt_1', name: 'Cloud Systems Engineer', description: 'Infrastructure, DevOps, and cloud reliability', attributes: { starting_salary: 95000 } },
      { id: 'opt_2', name: 'Full-Stack Product Developer', description: 'User-facing apps, end-to-end features', attributes: { starting_salary: 90000 } },
      { id: 'opt_3', name: 'Specialist Data Consultant', description: 'Client advisory, data pipelines, analytics', attributes: { starting_salary: 85000 } }
    ],
    criteria: [
      { id: 'crit_1', name: 'Market Demand & Growth', weight: 40.0 },
      { id: 'crit_2', name: 'Personal Interest & Passion', weight: 30.0 },
      { id: 'crit_3', name: 'Ease of Learning Curve', weight: 20.0 },
      { id: 'crit_4', name: 'Work-Life Balance', weight: 10.0 }
    ],
    ratings: [
      { option_id: 'opt_1', criterion_id: 'crit_1', rating: 9.0 },
      { option_id: 'opt_1', criterion_id: 'crit_2', rating: 8.0 },
      { option_id: 'opt_1', criterion_id: 'crit_3', rating: 6.0 },
      { option_id: 'opt_1', criterion_id: 'crit_4', rating: 7.0 },

      { option_id: 'opt_2', criterion_id: 'crit_1', rating: 8.5 },
      { option_id: 'opt_2', criterion_id: 'crit_2', rating: 9.0 },
      { option_id: 'opt_2', criterion_id: 'crit_3', rating: 7.0 },
      { option_id: 'opt_2', criterion_id: 'crit_4', rating: 7.5 },

      { option_id: 'opt_3', criterion_id: 'crit_1', rating: 7.0 },
      { option_id: 'opt_3', criterion_id: 'crit_2', rating: 6.5 },
      { option_id: 'opt_3', criterion_id: 'crit_3', rating: 5.0 },
      { option_id: 'opt_3', criterion_id: 'crit_4', rating: 6.0 }
    ],
    constraints: [
      { name: 'Min Base Compensation', attribute_key: 'starting_salary', operator: '>=', threshold: 80000 }
    ]
  },
  {
    id: 'laptop',
    title: 'Laptop / Hardware Selection',
    badge: 'Hardware',
    description: 'Evaluate computing devices across battery, build, performance, and budget.',
    options: [
      { id: 'opt_1', name: 'MacBook Pro 14 (M3)', description: 'Apple Silicon powerhouse', attributes: { price: 1999, battery_hours: 17 } },
      { id: 'opt_2', name: 'ThinkPad X1 Carbon Gen 12', description: 'Enterprise ultraportable', attributes: { price: 1450, battery_hours: 14 } },
      { id: 'opt_3', name: 'Dell XPS 13 OLED', description: 'Compact display-focused machine', attributes: { price: 1250, battery_hours: 9 } }
    ],
    criteria: [
      { id: 'crit_1', name: 'Processing Performance', weight: 35.0 },
      { id: 'crit_2', name: 'Battery Endurance', weight: 25.0 },
      { id: 'crit_3', name: 'Keyboard & Build Quality', weight: 20.0 },
      { id: 'crit_4', name: 'Price & Value', weight: 20.0 }
    ],
    ratings: [
      { option_id: 'opt_1', criterion_id: 'crit_1', rating: 9.5 },
      { option_id: 'opt_1', criterion_id: 'crit_2', rating: 9.5 },
      { option_id: 'opt_1', criterion_id: 'crit_3', rating: 9.0 },
      { option_id: 'opt_1', criterion_id: 'crit_4', rating: 6.5 },

      { option_id: 'opt_2', criterion_id: 'crit_1', rating: 8.0 },
      { option_id: 'opt_2', criterion_id: 'crit_2', rating: 8.5 },
      { option_id: 'opt_2', criterion_id: 'crit_3', rating: 9.5 },
      { option_id: 'opt_2', criterion_id: 'crit_4', rating: 8.0 },

      { option_id: 'opt_3', criterion_id: 'crit_1', rating: 8.0 },
      { option_id: 'opt_3', criterion_id: 'crit_2', rating: 6.0 },
      { option_id: 'opt_3', criterion_id: 'crit_3', rating: 7.5 },
      { option_id: 'opt_3', criterion_id: 'crit_4', rating: 8.5 }
    ],
    constraints: [
      { name: 'Min Battery Life', attribute_key: 'battery_hours', operator: '>=', threshold: 10 }
    ]
  },
  {
    id: 'job_offer',
    title: 'Job Offer Comparison',
    badge: 'Career',
    description: 'Weigh job opportunities on compensation, culture, team leadership, and autonomy.',
    options: [
      { id: 'opt_1', name: 'High-Growth Startup', description: 'Fast pace, equity upside, broad ownership', attributes: { commute_mins: 15 } },
      { id: 'opt_2', name: 'Established Tech Enterprise', description: 'Stability, robust benefits, large engineering org', attributes: { commute_mins: 45 } },
      { id: 'opt_3', name: 'Boutique Specialized Agency', description: 'Diverse client portfolio, tight-knit team', attributes: { commute_mins: 20 } }
    ],
    criteria: [
      { id: 'crit_1', name: 'Growth & Mentorship', weight: 35.0 },
      { id: 'crit_2', name: 'Compensation & Benefits', weight: 30.0 },
      { id: 'crit_3', name: 'Workplace Culture', weight: 20.0 },
      { id: 'crit_4', name: 'Commute & Flexibility', weight: 15.0 }
    ],
    ratings: [
      { option_id: 'opt_1', criterion_id: 'crit_1', rating: 9.0 },
      { option_id: 'opt_1', criterion_id: 'crit_2', rating: 7.5 },
      { option_id: 'opt_1', criterion_id: 'crit_2', rating: 8.0 },
      { option_id: 'opt_1', criterion_id: 'crit_4', rating: 8.5 },

      { option_id: 'opt_2', criterion_id: 'crit_1', rating: 7.5 },
      { option_id: 'opt_2', criterion_id: 'crit_2', rating: 9.5 },
      { option_id: 'opt_2', criterion_id: 'crit_3', rating: 7.0 },
      { option_id: 'opt_2', criterion_id: 'crit_4', rating: 6.0 },

      { option_id: 'opt_3', criterion_id: 'crit_1', rating: 7.0 },
      { option_id: 'opt_3', criterion_id: 'crit_2', rating: 7.0 },
      { option_id: 'opt_3', criterion_id: 'crit_3', rating: 8.5 },
      { option_id: 'opt_3', criterion_id: 'crit_4', rating: 8.0 }
    ],
    constraints: [
      { name: 'Max Commute (Minutes)', attribute_key: 'commute_mins', operator: '<=', threshold: 60 }
    ]
  },
  {
    id: 'skill_course',
    title: 'Course or Skill to Learn Next',
    badge: 'Education',
    description: 'Decide what technology or certification will maximize your learning return on investment.',
    options: [
      { id: 'opt_1', name: 'System Design & Distributed Architectures', description: 'Advanced backend patterns and scaling', attributes: { hours_needed: 60 } },
      { id: 'opt_2', name: 'Full-Stack TypeScript & Next.js', description: 'Modern reactive frontend development', attributes: { hours_needed: 45 } },
      { id: 'opt_3', name: 'DevOps, Docker & Kubernetes Foundations', description: 'Containerization and deployment pipelines', attributes: { hours_needed: 50 } }
    ],
    criteria: [
      { id: 'crit_1', name: 'Direct Resume Impact', weight: 40.0 },
      { id: 'crit_2', name: 'Practical Utility in Current Role', weight: 30.0 },
      { id: 'crit_3', name: 'Quality of Available Resources', weight: 20.0 },
      { id: 'crit_4', name: 'Enjoyment of Topic', weight: 10.0 }
    ],
    ratings: [
      { option_id: 'opt_1', criterion_id: 'crit_1', rating: 9.0 },
      { option_id: 'opt_1', criterion_id: 'crit_2', rating: 8.5 },
      { option_id: 'opt_1', criterion_id: 'crit_3', rating: 7.5 },
      { option_id: 'opt_1', criterion_id: 'crit_4', rating: 8.0 },

      { option_id: 'opt_2', criterion_id: 'crit_1', rating: 8.0 },
      { option_id: 'opt_2', criterion_id: 'crit_2', rating: 9.0 },
      { option_id: 'opt_2', criterion_id: 'crit_3', rating: 9.0 },
      { option_id: 'opt_2', criterion_id: 'crit_4', rating: 7.5 },

      { option_id: 'opt_3', criterion_id: 'crit_1', rating: 8.5 },
      { option_id: 'opt_3', criterion_id: 'crit_2', rating: 7.5 },
      { option_id: 'opt_3', criterion_id: 'crit_3', rating: 8.0 },
      { option_id: 'opt_3', criterion_id: 'crit_4', rating: 7.0 }
    ],
    constraints: [
      { name: 'Max Hours Required', attribute_key: 'hours_needed', operator: '<=', threshold: 75 }
    ]
  },
  {
    id: 'project_idea',
    title: 'Side Project or Business Idea',
    badge: 'Projects',
    description: 'Prioritize project concepts by market feasibility, technical excitement, and time to launch.',
    options: [
      { id: 'opt_1', name: 'Micro-SaaS Productivity Tool', description: 'Niche subscription service for professionals', attributes: { weeks_to_mvp: 6 } },
      { id: 'opt_2', name: 'Open-Source Developer CLI', description: 'Developer productivity tool with GitHub traction', attributes: { weeks_to_mvp: 3 } },
      { id: 'opt_3', name: 'Interactive Educational Course', description: 'Hands-on guided tutorials with code sandboxes', attributes: { weeks_to_mvp: 8 } }
    ],
    criteria: [
      { id: 'crit_1', name: 'Speed to Market / MVP', weight: 35.0 },
      { id: 'crit_2', name: 'Monetization Potential', weight: 35.0 },
      { id: 'crit_3', name: 'Technical Excitement & Fun', weight: 20.0 },
      { id: 'crit_4', name: 'Low Operational Maintenance', weight: 10.0 }
    ],
    ratings: [
      { option_id: 'opt_1', criterion_id: 'crit_1', rating: 7.0 },
      { option_id: 'opt_1', criterion_id: 'crit_2', rating: 8.5 },
      { option_id: 'opt_1', criterion_id: 'crit_3', rating: 8.5 },
      { option_id: 'opt_1', criterion_id: 'crit_4', rating: 6.5 },

      { option_id: 'opt_2', criterion_id: 'crit_1', rating: 9.0 },
      { option_id: 'opt_2', criterion_id: 'crit_2', rating: 4.0 },
      { option_id: 'opt_2', criterion_id: 'crit_3', rating: 9.5 },
      { option_id: 'opt_2', criterion_id: 'crit_4', rating: 8.0 },

      { option_id: 'opt_3', criterion_id: 'crit_1', rating: 6.0 },
      { option_id: 'opt_3', criterion_id: 'crit_2', rating: 8.0 },
      { option_id: 'opt_3', criterion_id: 'crit_3', rating: 7.5 },
      { option_id: 'opt_3', criterion_id: 'crit_4', rating: 7.0 }
    ],
    constraints: [
      { name: 'Max Weeks to MVP', attribute_key: 'weeks_to_mvp', operator: '<=', threshold: 10 }
    ]
  }
];
