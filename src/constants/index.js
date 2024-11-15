export const navLinks = [
    {
      id: 1,
      name: 'Home',
      href: '#home',
    },
    {
      id: 2,
      name: 'About',
      href: '#about',
    },
    {
      id: 3,
      name: 'Projects',
      href: '#projects',
    },
    {
      id: 4,
      name: 'Clients',
      href: '#clients',
    },
    {
      id: 5,
      name: 'Work',
      href: '#work',
    },
    {
      id: 6,
      name: 'Contact',
      href: '#contact',
    },
  ];
  
  export const clientReviews = [
    {
      id: 1,
      name: 'Godson Ozioma',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/review1.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      review:
        'It was a pleasure working with Somunachimso Nzenwa during our time at the University of Salford. He is an exceptional individual with a deep understanding of software engineering principles, particularly in mobile, web, and game development. His problem-solving skills and dedication to his craft make him a valuable team player, and his leadership abilities helped drive multiple projects to success, even under tight deadlines. Somunachimso consistently demonstrated a passion for learning and collaboration, which has positively impacted both his teammates and the final outcomes of his work. I highly recommend him for any software engineering role.',
    },
    {
      id: 2,
      name: 'Emmanuel Uduma',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/review2.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      review:
      'I would like to recommend Somuna.He has shown class and excellence in his ability to team bond and carry on a team to the achievement of thier expected goals. His organisational skills coupled with his leadership skills has proven useful and insightful in various projects and activities we had partaken in. This has lead not only to increased productivity but excellence in product delivery even in situations of immerse pressure. I must say I have richly benefited from this peculiarities of his in the areas of mobile Development, Web Developemnt and game development.'
    },
    {
      id: 3,
      name: 'Israel Karibo Alalibo',
      position: 'Placement Engineer at Dematic',
      img: 'assets/review3.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      review:
      'Somuna is very determined and open to help out in any way he can. Personally received help from Somunachimso with various tricky concepts in programming and that really helped my understanding.\nWith in depth understanding of mobile, CI & CD, web and game development, Somuna’s technical skills are one of the best I’ve seen. \nAlso his teamwork and communication skills are brilliant along side his ability to work under pressure.\nHe is a great leader with exceptional leadership qualities.\nHe is skilful, kind and resourceful. Ready to make an impact in the cooperate world!'
    },
    {
      id: 4,
      name: 'Odiepriye Graham-Douglas',
      position: 'Full Stack Software Developer at The Software Institute',
      img: 'assets/review4.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      review:
      'I am pleased to recommend Somuna, whose expertise in mobile, web, and game development, as well as CI & CD practices, has been truly impressive. During our time together, we’ve worked together on a website and application using PHP and Java respectively at university, Somuna demonstrated exceptional technical skills and a strong grasp of development practices.\nIn our Java project, Somuna was instrumental in designing and implementing robust solutions. His deep understanding of Java, combined with his ability to tackle complex coding challenges, significantly contributed to the project’s success. His attention to detail and commitment to best practices were evident throughout the development process.\nSomunas experience with CI & CD practices was also a major asset. He effectively managed our continuous integration and delivery processes, ensuring smooth and efficient deployment cycles. His skills in automating workflows and maintaining high-quality standards greatly improved our projects development efficiency.\nSomunas technical proficiency, problem-solving abilities, and dedication to his work make him a standout professional. I highly recommend him for any role requiring expertise in development and CI & CD practices.'
    },
    {
      id: 5,
      name: 'Solomon Adukwu',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/review4.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      review:
        'There’s a lot about Somunachimso that stands out. He is hardworking and a goal getter. I have worked with him on various projects in the past and he is definitely a team player. His tenacity to exceed expectations with allocated projects is very admirable. He is very ambitious and a go getter and I know he would be a great addition to any team. 👍',
    },
    {
      id: 6,
      name: 'Aleixo Carvalho',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/review4.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      review:
        'I can confidently testify to Somuna’s expertise in mobile, web, and game development, as well as his solid understanding of CI/CD processes. He has shown proficiency in building and deploying scalable applications, utilizing modern tools and frameworks to deliver high-quality results. His ability to automate and streamline workflows through CI/CD has greatly enhanced development efficiency.\nSomuna is also an excellent collaborator and team player, effectively communicating and working with others to achieve project goals. He thrives under pressure, maintaining focus and delivering results while exhibiting strong leadership skills, guiding teams through challenges with confidence and clarity.',
    }
  ];
  
  export const myProjects = [
    {
      title: 'Real Estate Website',
      desc: 'A platform for users to list, view, like, reserve, and purchase real estate',
      subdesc:
        'Built as a unique Software-as-a-Service app with Node.js, Tailwind CSS, MongoDB, Express, and React. The website is designed for optimal performance and scalability.',
      href: 'https://www.youtube.com/@bullfighter.inc.',
      texture: '/textures/project/project1.mp4',
      logo: '/assets/project-logo1.png',
      logoStyle: {
        backgroundColor: '#2A1816',
        border: '0.2px solid #36201D',
        boxShadow: '0px 0px 60px 0px #AA3C304D',
      },
      spotlight: '/assets/spotlight1.png',
      tags: [
        {
          id: 1,
          name: 'React.js',
          path: '/assets/react.svg',
        },
        {
          id: 2,
          name: 'TailwindCSS',
          path: 'assets/tailwindcss.png',
        },
        {
          id: 3,
          name: 'TypeScript',
          path: '/assets/typescript.png',
        },
        {
          id: 4,
          name: 'Framer Motion',
          path: '/assets/framer.png',
        },
      ],
    },
    {
      title: 'LiveDoc - Real-Time Google Docs Clone',
      desc: 'LiveDoc is a powerful collaborative app that elevates the capabilities of real-time document editing. As an enhanced version of Google Docs, It supports millions of collaborators simultaneously, ensuring that every change is captured instantly and accurately.',
      subdesc:
        'With LiveDoc, users can experience the future of collaboration, where multiple contributors work together in real time without any lag, by using Next.js and Liveblocks newest features.',
      href: 'https://www.youtube.com/watch?v=y5vE8y_f_OM',
      texture: '/textures/project/project2.mp4',
      logo: '/assets/project-logo2.png',
      logoStyle: {
        backgroundColor: '#13202F',
        border: '0.2px solid #17293E',
        boxShadow: '0px 0px 60px 0px #2F6DB54D',
      },
      spotlight: '/assets/spotlight2.png',
      tags: [
        {
          id: 1,
          name: 'React.js',
          path: '/assets/react.svg',
        },
        {
          id: 2,
          name: 'TailwindCSS',
          path: 'assets/tailwindcss.png',
        },
        {
          id: 3,
          name: 'TypeScript',
          path: '/assets/typescript.png',
        },
        {
          id: 4,
          name: 'Framer Motion',
          path: '/assets/framer.png',
        },
      ],
    },
    {
      title: 'CarePulse - Health Management System',
      desc: 'An innovative healthcare platform designed to streamline essential medical processes. It simplifies patient registration, appointment scheduling, and medical record management, providing a seamless experience for both healthcare providers and patients.',
      subdesc:
        'With a focus on efficiency, CarePulse integrantes complex forms and SMS notifications, by using Next.js, Appwrite, Twillio and Sentry that enhance operational workflows.',
      href: 'https://www.youtube.com/watch?v=lEflo_sc82g',
      texture: '/textures/project/project3.mp4',
      logo: '/assets/project-logo3.png',
      logoStyle: {
        backgroundColor: '#60f5a1',
        background:
          'linear-gradient(0deg, #60F5A150, #60F5A150), linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(208, 213, 221, 0.8) 100%)',
        border: '0.2px solid rgba(208, 213, 221, 1)',
        boxShadow: '0px 0px 60px 0px rgba(35, 131, 96, 0.3)',
      },
      spotlight: '/assets/spotlight3.png',
      tags: [
        {
          id: 1,
          name: 'React.js',
          path: '/assets/react.svg',
        },
        {
          id: 2,
          name: 'TailwindCSS',
          path: 'assets/tailwindcss.png',
        },
        {
          id: 3,
          name: 'TypeScript',
          path: '/assets/typescript.png',
        },
        {
          id: 4,
          name: 'Framer Motion',
          path: '/assets/framer.png',
        },
      ],
    },
    {
      title: 'Horizon - Online Banking Platform',
      desc: 'Horizon is a comprehensive online banking platform that offers users a centralized finance management dashboard. It allows users to connect multiple bank accounts, monitor real-time transactions, and seamlessly transfer money to other users.',
      subdesc:
        'Built with Next.js 14 Appwrite, Dwolla and Plaid, Horizon ensures a smooth and secure banking experience, tailored to meet the needs of modern consumers.',
      href: 'https://www.youtube.com/watch?v=PuOVqP_cjkE',
      texture: '/textures/project/project4.mp4',
      logo: '/assets/project-logo4.png',
      logoStyle: {
        backgroundColor: '#0E1F38',
        border: '0.2px solid #0E2D58',
        boxShadow: '0px 0px 60px 0px #2F67B64D',
      },
      spotlight: '/assets/spotlight4.png',
      tags: [
        {
          id: 1,
          name: 'React.js',
          path: '/assets/react.svg',
        },
        {
          id: 2,
          name: 'TailwindCSS',
          path: 'assets/tailwindcss.png',
        },
        {
          id: 3,
          name: 'TypeScript',
          path: '/assets/typescript.png',
        },
        {
          id: 4,
          name: 'Framer Motion',
          path: '/assets/framer.png',
        },
      ],
    },
    {
      title: 'Imaginify - AI Photo Manipulation App',
      desc: 'Imaginify is a groundbreaking Software-as-a-Service application that empowers users to create stunning photo manipulations using AI technology. With features like AI-driven image editing, a payments system, and a credits-based model.',
      subdesc:
        'Built with Next.js 14, Cloudinary AI, Clerk, and Stripe, Imaginify combines cutting-edge technology with a user-centric approach. It can be turned into a side income or even a full-fledged business.',
      href: 'https://www.youtube.com/watch?v=Ahwoks_dawU',
      texture: '/textures/project/project5.mp4',
      logo: '/assets/project-logo5.png',
      logoStyle: {
        backgroundColor: '#1C1A43',
        border: '0.2px solid #252262',
        boxShadow: '0px 0px 60px 0px #635BFF4D',
      },
      spotlight: '/assets/spotlight5.png',
      tags: [
        {
          id: 1,
          name: 'React.js',
          path: '/assets/react.svg',
        },
        {
          id: 2,
          name: 'TailwindCSS',
          path: 'assets/tailwindcss.png',
        },
        {
          id: 3,
          name: 'TypeScript',
          path: '/assets/typescript.png',
        },
        {
          id: 4,
          name: 'Framer Motion',
          path: '/assets/framer.png',
        },
      ],
    },
  ];
  
  export const calculateSizes = (isSmall, isMobile, isTablet) => {
    return {
      deskScale: isSmall ? 0.05 : isMobile ? 0.06 : 0.065,
      deskPosition: isMobile ? [0.5, -4.5, 0] : [0.25, -5.5, 0],
      cubePosition: isSmall ? [4, -5, 0] : isMobile ? [5, -5, 0] : isTablet ? [5, -5, 0] : [9, -5.5, 0],
      reactLogoPosition: isSmall ? [3, 4, 0] : isMobile ? [5, 4, 0] : isTablet ? [5, 4, 0] : [12, 3, 0],
      ringPosition: isSmall ? [-5, 7, 0] : isMobile ? [-10, 10, 0] : isTablet ? [-12, 10, 0] : [-24, 10, 0],
      targetPosition: isSmall ? [-5, -10, -10] : isMobile ? [-9, -10, -10] : isTablet ? [-11, -7, -10] : [-13, -13, -10],
    };
  };
  
  export const workExperiences = [
    {
      id: 1,
      name: 'Framer',
      pos: 'Lead Web Developer',
      duration: '2022 - Present',
      title: "Framer serves as my go-to tool for creating interactive prototypes. I use it to bring designs to  life, allowing stakeholders to experience the user flow and interactions before development.",
      icon: '/assets/framer.svg',
      animation: 'victory',
    },
    {
      id: 2,
      name: 'Figma',
      pos: 'Web Developer',
      duration: '2020 - 2022',
      title: "Figma is my collaborative design platform of choice. I utilize it to work seamlessly with team members and clients, facilitating real-time feedback and design iterations. Its cloud-based.",
      icon: '/assets/figma.svg',
      animation: 'clapping',
    },
    {
      id: 3,
      name: 'Notion',
      pos: 'Junior Web Developer',
      duration: '2019 - 2020',
      title: "Notion helps me keep my projects organized. I use it for project management, task tracking, and as a central hub for documentation, ensuring that everything from design notes to.",
      icon: '/assets/notion.svg',
      animation: 'salute',
    },
  ];