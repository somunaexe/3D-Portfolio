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
      rating: 5,
      review:
        'It was a pleasure working with Somunachimso Nzenwa during our time at the University of Salford. He is an exceptional individual with a deep understanding of software engineering principles, particularly in mobile, web, and game development. His problem-solving skills and dedication to his craft make him a valuable team player, and his leadership abilities helped drive multiple projects to success, even under tight deadlines. Somunachimso consistently demonstrated a passion for learning and collaboration, which has positively impacted both his teammates and the final outcomes of his work. I highly recommend him for any software engineering role.',
    },
    {
      id: 2,
      name: 'Emmanuel Uduma',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/review2.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      rating: 5,
      review:
      'I would like to recommend Somuna.He has shown class and excellence in his ability to team bond and carry on a team to the achievement of thier expected goals. His organisational skills coupled with his leadership skills has proven useful and insightful in various projects and activities we had partaken in. This has lead not only to increased productivity but excellence in product delivery even in situations of immerse pressure. I must say I have richly benefited from this peculiarities of his in the areas of mobile Development, Web Developemnt and game development.'
    },
    {
      id: 3,
      name: 'Israel Karibo Alalibo',
      position: 'Placement Engineer at Dematic',
      img: 'assets/review3.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      rating: 5,
      review:
      'Somuna is very determined and open to help out in any way he can. Personally received help from Somunachimso with various tricky concepts in programming and that really helped my understanding.\nWith in depth understanding of mobile, CI & CD, web and game development, Somuna’s technical skills are one of the best I’ve seen. \nAlso his teamwork and communication skills are brilliant along side his ability to work under pressure.\nHe is a great leader with exceptional leadership qualities.\nHe is skilful, kind and resourceful. Ready to make an impact in the cooperate world!'
    },
    {
      id: 4,
      name: 'Odiepriye Graham-Douglas',
      position: 'Full Stack Software Developer at The Software Institute',
      img: 'assets/ody.jpeg',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      rating: 5,
      review:
      'I am pleased to recommend Somuna, whose expertise in mobile, web, and game development, as well as CI & CD practices, has been truly impressive. During our time together, we’ve worked together on a website and application using PHP and Java respectively at university, Somuna demonstrated exceptional technical skills and a strong grasp of development practices.\nIn our Java project, Somuna was instrumental in designing and implementing robust solutions. His deep understanding of Java, combined with his ability to tackle complex coding challenges, significantly contributed to the project’s success. His attention to detail and commitment to best practices were evident throughout the development process.\nSomunas experience with CI & CD practices was also a major asset. He effectively managed our continuous integration and delivery processes, ensuring smooth and efficient deployment cycles. His skills in automating workflows and maintaining high-quality standards greatly improved our projects development efficiency.\nSomunas technical proficiency, problem-solving abilities, and dedication to his work make him a standout professional. I highly recommend him for any role requiring expertise in development and CI & CD practices.'
    },
    {
      id: 5,
      name: 'Solomon Adukwu',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/solomon.jpeg',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      rating: 5,
      review:
        'There’s a lot about Somunachimso that stands out. He is hardworking and a goal getter. I have worked with him on various projects in the past and he is definitely a team player. His tenacity to exceed expectations with allocated projects is very admirable. He is very ambitious and a go getter and I know he would be a great addition to any team. 👍',
    },
    {
      id: 6,
      name: 'Aleixo Carvalho',
      position: 'Software Engineering Graduate at University of Salford',
      img: 'assets/review4.png',
      link: 'https://www.linkedin.com/in/somunachimso-nzenwa-a738a1192/details/recommendations/?detailScreenTabIndex=0',
      rating: 5,
      review:
        'I can confidently testify to Somuna’s expertise in mobile, web, and game development, as well as his solid understanding of CI/CD processes. He has shown proficiency in building and deploying scalable applications, utilizing modern tools and frameworks to deliver high-quality results. His ability to automate and streamline workflows through CI/CD has greatly enhanced development efficiency.\nSomuna is also an excellent collaborator and team player, effectively communicating and working with others to achieve project goals. He thrives under pressure, maintaining focus and delivering results while exhibiting strong leadership skills, guiding teams through challenges with confidence and clarity.',
    }
  ];

  export const myProjects = [
    {
      title: "Online Clothing Store w/ Stripe",
      desc: "An ASP.Net-based shopping platform with secure payment integrations and database management.",
      subdesc: "Built using ASP.Net, C#, and SQL Server with MVC pattern to ensure modularity. Integrated a secure payment gateway via Stripe, allowing transactions with cards, Revolut, and Klarna.",
      href: null,
      texture: "/textures/project/shopping-store.mp4",
      logo: "/assets/project-logo-shopping-store.png",
      logoStyle: {
        backgroundColor: "#F0F0F0",
        border: "0.2px solid #CCCCCC",
        boxShadow: "0px 0px 60px 0px #CCCCCC4D",
      },
      spotlight: "/assets/spotlight1.png",
      tags: [
        {name: "ASP.Net", path: "/assets/aspnet.png" },
        {name: "C#", path: "/assets/csharp.svg" },
        {name: "SQL Server", path: "/assets/sqlserver.png" },
        {name: "HTML", path: "/assets/html.svg" },
        {name: "CSS", path: "/assets/css.svg" },
      ],
    },
    {
      title: "Charging Station Locator",
      desc: "A web app for locating EV charging stations using geolocation and AJAX.",
      subdesc: "Developed with PHP and MySQL, featuring a map-based search and user authentication. Scaled to support 2000 users simultaneously.",
      href: null,
      texture: "/textures/project/charging-station.mp4",
      logo: "/assets/project-logo-charging-station.png",
      logoStyle: {
        backgroundColor: "#E8F5E9",
        border: "0.2px solid #C8E6C9",
        boxShadow: "0px 0px 60px 0px #81C7844D",
      },
      spotlight: "/assets/spotlight3.png",
      tags: [
        {name: "PHP", path: "/assets/php.svg" },
        {name: "JavaScript", path: "/assets/javascript.svg" },
        {name: "MySQL", path: "/assets/mysql.svg" },
        {name: "HTML", path: "/assets/html.svg" },
        {name: "CSS", path: "/assets/css.svg" },
        {name: "Bootstrap", path: "/assets/bootstrap.png" },
      ],
    },
    {
      title: "First-Person Shooter Zombie Virtual Reality Game",
      desc: "A cutting-edge VR game with immersive gameplay and advanced AI.",
      subdesc: "Implemented advanced AI for enemy behavior and intuitive HUD elements using Unity and Blender.",
      href: null,
      texture: "/textures/project/vr-fps-game.mp4",
      logo: "/assets/project-logo-vr-fps.png",
      logoStyle: {
        backgroundColor: "#000000",
        border: "0.2px solid #333333",
        boxShadow: "0px 0px 60px 0px #5555554D",
      },
      spotlight: "/assets/spotlight3.png",
      tags: [
        {name: "Unity", path: "/assets/unity.svg" },
        {name: "C#", path: "/assets/csharp.svg" },
        {name: "Blender", path: "/assets/blender.png" },
      ],
    },
    {
      title: "Laptop Game: Endless Running 3D Game",
      desc: "A Unity-based endless runner game with combat and score systems.",
      subdesc: "Integrated coroutines for animations and player mechanics, with attack features and coin collection gameplay.",
      href: null,
      texture: "/textures/project/endless-runner.mp4",
      logo: "/assets/project-logo-endless-runner.png",
      logoStyle: {
        backgroundColor: "#FCE4EC",
        border: "0.2px solid #F48FB1",
        boxShadow: "0px 0px 60px 0px #F062924D",
      },
      spotlight: "/assets/spotlight1.png",
      tags: [
        {name: "Unity", path: "/assets/unity.svg" },
        {name: "C#", path: "/assets/csharp.svg" },
      ],
    },
    {
      title: "Mobile Science Game",
      desc: "An educational mobile game for iOS and Android platforms.",
      subdesc: "Built with Kotlin and Swift to teach science in a fun and interactive way, featuring touch gestures and a reward system.",
      href: null,
      texture: "/textures/project/science-game.mp4",
      logo: "/assets/project-logo-science-game.png",
      logoStyle: {
        backgroundColor: "#BBDEFB",
        border: "0.2px solid #90CAF9",
        boxShadow: "0px 0px 60px 0px #64B5F64D",
      },
      spotlight: "/assets/spotlight4.png",
      tags: [
        {name: "Kotlin", path: "/assets/kotlin.svg" },
        {name: "Swift", path: "/assets/swift.svg" },
      ],
    },
    {
      title: "Online Clothing Store",
      desc: "A Flutter-based e-commerce app for buying and recycling clothing.",
      subdesc: "Implemented search algorithms, filter, and sort functionality. Integrated robust security and a reward system for discounts.",
      href: null,
      texture: "/textures/project/online-store.mp4",
      logo: "/assets/project-logo-clothing-store.png",
      logoStyle: {
        backgroundColor: "#FBE9E7",
        border: "0.2px solid #FFAB91",
        boxShadow: "0px 0px 60px 0px #FF8A654D",
      },
      spotlight: "/assets/spotlight5.png",
      tags: [
        {name: "Flutter", path: "/assets/flutter.svg" },
        {name: "Dart", path: "/assets/dart.svg" },
        {name: "Firebase", path: "/assets/firebase.svg" },
      ],
    },
    {
      title: "Note Organization Website",
      desc: "A web app that helps users organize and manage notes with tagging and searching features.",
      subdesc: "Developed with React, TypeScript, and Bootstrap. Allows users to create, edit, search, and delete notes.",
      href: null,
      texture: "/textures/project/note-organization.mp4",
      logo: "/assets/project-logo-note-organization.png",
      logoStyle: {
        backgroundColor: "#E1F5FE",
        border: "0.2px solid #81D4FA",
        boxShadow: "0px 0px 60px 0px #4FC3F74D",
      },
      spotlight: "/assets/spotlight2.png",
      tags: [
        {name: "React.js", path: "/assets/react.svg" },
        {name: "TypeScript", path: "/assets/typescript.png" },
        {name: "Bootstrap", path: "/assets/bootstrap.png" },
        {name: "HTML", path: "/assets/html.svg" },
        {name: "CSS", path: "/assets/css.svg" },
      ],
    },
    {
      title: "Regex Script",
      desc: "A JavaScript-based script for efficient text parsing using regular expressions.",
      subdesc: "Created a script that parses and manipulates complex text patterns across various web applications. Designed for scalability and accuracy.",
      href: null,
      texture: "/textures/project/regex-script.mp4",
      logo: "/assets/project-logo-regex-script.png",
      logoStyle: {
        backgroundColor: "#FFFFFF",
        border: "0.2px solid #E0E0E0",
        boxShadow: "0px 0px 60px 0px #BDBDBD4D",
      },
      spotlight: "/assets/spotlight3.png",
      tags: [
        { id: 1, name: "JavaScript", path: "/assets/javascript.svg" },
      ],
    },
    {
      title: "3D Voxel Game Engine",
      desc: "A Java-based 3D voxel game engine for rendering voxel environments.",
      subdesc: "Engineered a 3D voxel engine using LWJGL to render and interact with voxel-based environments.",
      href: null,
      texture: "/textures/project/voxel-game-engine.mp4",
      logo: "/assets/project-logo-voxel-game-engine.png",
      logoStyle: {
        backgroundColor: "#F5F5F5",
        border: "0.2px solid #CCCCCC",
        boxShadow: "0px 0px 60px 0px #BDBDBD4D",
      },
      spotlight: "/assets/spotlight3.png",
      tags: [
        {name: "Java", path: "/assets/java.svg" },
        {name: "LWJGL", path: "/assets/lwjgl.png" },
      ],
    },
    {
      title: "Python Bundle",
      desc: "A Python bundle with various utilities like automation, binary search, and graph plotting.",
      subdesc: "Created a text automation script, a binary search algorithm, and a graph plotting tool using Matplotlib.",
      href: null,
      texture: "/textures/project/python-bundle.mp4",
      logo: "/assets/project-logo-python-bundle.png",
      logoStyle: {
        backgroundColor: "#E8F5E9",
        border: "0.2px solid #A5D6A7",
        boxShadow: "0px 0px 60px 0px #81C7844D",
      },
      spotlight: "/assets/spotlight2.png",
      tags: [
        {name: "Python", path: "/assets/python.svg" },
        {name: "Matplotlib", path: "/assets/matplotlib.png" },
      ],
    },
    {
      title: "Real-Time Anomaly Detector",
      desc: "A Python-based anomaly detection system to identify outliers in continuous data streams.",
      subdesc: "Developed a Z-score based anomaly detection system using Python's Numpy and Matplotlib for real-time analysis. Features real-time data simulation with seasonal patterns and injected noise for robust testing.",
      href: null,
      texture: "/textures/project/anomaly.mp4",
      logo: "/assets/project-logo-anomaly-detector.png",
      logoStyle: {
        backgroundColor: "#FFEB3B",
        border: "0.2px solid #FBC02D",
        boxShadow: "0px 0px 60px 0px rgba(255, 193, 7, 0.5)",
      },
      spotlight: "/assets/spotlight2.png",
      tags: [
        {name: "Python", path: "/assets/python.svg" },
        {name: "Numpy", path: "/assets/numpy.png" },
        {name: "Matplotlib", path: "/assets/matplotlib.png" },
      ],
    },
    {
      title: "Cryptocurrency WebApp",
      desc: "A web application for tracking cryptocurrency trends using React, Redux, and Chart.js.",
      subdesc: "The app fetches real-time cryptocurrency data using React API and displays trends using Chart.js. Features a responsive design and robust debugging tools like Chrome Dev Tools and React Dev Tools Extension.",
      href: "https://github.com/your-username/crypto-webapp", // Replace with actual link if available
      texture: "/textures/project/crypto.mp4",
      logo: "/assets/project-logo-crypto.png",
      logoStyle: {
        backgroundColor: "#4CAF50",
        border: "0.2px solid #388E3C",
        boxShadow: "0px 0px 60px 0px rgba(76, 175, 80, 0.5)",
      },
      spotlight: "/assets/spotlight4.png",
      tags: [
        {name: "React.js", path: "/assets/react.svg" },
        {name: "Redux", path: "/assets/redux.png" },
        {name: "Chart.js", path: "/assets/chartjs.png" },
        {name: "HTML", path: "/assets/html.svg" },
        {name: "CSS", path: "/assets/css.svg" },
      ],
    },
    {
      title: "Custom CLI Tool",
      desc: "A command-line interface tool built from scratch using Node.js.",
      subdesc: "Implemented functionalities like argument parsing, input validation, and error handling. Packaged as a globally installable npm package, designed for ease of use and scalability.",
      href: "https://github.com/your-username/cli-tool", // Replace with actual link
      texture: "/textures/project/cli-tool.mp4",
      logo: "/assets/project-logo-cli.png",
      logoStyle: {
        backgroundColor: "#333333",
        border: "0.2px solid #555555",
        boxShadow: "0px 0px 60px 0px rgba(0, 0, 0, 0.5)",
      },
      spotlight: "/assets/spotlight3.png",
      tags: [
        {name: "JavaScript", path: "/assets/javascript.svg" },
        {name: "Node.js", path: "/assets/node.png" },
      ],
    },
    {
      title: "Real Estate Website",
      desc: "A real estate platform allowing users to list, view, like, reserve, and purchase properties.",
      subdesc: "Built with a microservices architecture using HTML, MongoDB, Express, React, Node, and Tailwind CSS. Includes user authentication, password hashing, and a responsive design.",
      href: "https://github.com/your-username/real-estate-website", // Replace with actual link
      texture: "/textures/project/real-estate-website.mp4",
      logo: "/assets/project-logo-real-estate.png",
      logoStyle: {
        backgroundColor: "#2C3E50",
        border: "0.2px solid #34495E",
        boxShadow: "0px 0px 60px 0px rgba(44, 62, 80, 0.5)",
      },
      spotlight: "/assets/spotlight5.png",
      tags: [
        {name: "React.js", path: "/assets/react.svg" },
        {name: "Node.js", path: "/assets/node.png" },
        {name: "MongoDB", path: "/assets/mongodb.jfif" },
        {name: "Tailwind CSS", path: "/assets/tailwindcss.png" },
        {name: "Express.js", path: "/assets/express.png" },
        {name: "HTML", path: "/assets/html.svg" },
        {name: "CSS", path: "/assets/css.svg" },
      ],
    },
    {
      title: "Mario Kart Clone Web Game",
      desc: "An open-source web-based game inspired by Mario Kart, with game mechanics and user interface built using React and Redux.",
      subdesc: "Contributed to implementing game mechanics and ensuring responsive design and user-friendly interactions. Collaborated via GitHub for version control and open-source practices.",
      href: "https://github.com/your-username/mario-kart-clone", // Replace with actual link
      texture: "/textures/project/mario-kart-clone.mp4",
      logo: "/assets/project-logo-mario-kart.png",
      logoStyle: {
        backgroundColor: "#E74C3C",
        border: "0.2px solid #C0392B",
        boxShadow: "0px 0px 60px 0px rgba(231, 76, 60, 0.5)",
      },
      spotlight: "/assets/spotlight4.png",
      tags: [
        {name: "React.js", path: "/assets/react.svg" },
        {name: "Redux", path: "/assets/redux.png" },
        {name: "HTML", path: "/assets/html.svg" },
        {name: "CSS", path: "/assets/css.svg" },
        {name: "JavaScript", path: "/assets/javascript.svg" },
      ],
    }    
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