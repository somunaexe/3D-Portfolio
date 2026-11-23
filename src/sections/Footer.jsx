// Everything this site is built with, front end and the Ezem chatbot behind it. Add a row here to list a new tool.
const technologies = [
  { name: 'React', icon: '/assets/react.svg' },
  { name: 'Vite', icon: '/assets/vite.png' },
  { name: 'JavaScript', icon: '/assets/javascript.svg' },
  { name: 'Three.js', icon: '/assets/three.png' },
  { name: 'Tailwind CSS', icon: '/assets/tailwindcss.png' },
  { name: 'Python', icon: '/assets/python.svg' },
  { name: 'FastAPI', icon: '/assets/fastapi.svg' },
  { name: 'LangChain', icon: '/assets/langchain.svg' },
  { name: 'ChromaDB', icon: '/assets/chromadb.svg' },
  { name: 'Redis', icon: '/assets/redis.svg' },
  { name: 'OpenAI', icon: '/assets/openai.svg' },
  { name: 'Docker', icon: '/assets/docker.png' },
  { name: 'Railway', icon: '/assets/railway.svg' },
  { name: 'AWS', icon: '/assets/aws-light.png' },
  { name: 'GitHub Actions', icon: '/assets/githubactions.svg' },
  { name: 'Git', icon: '/assets/git.png' },
]

const Footer = () => {
  return (
    <footer className="c-space pt-7 pb-3 border-t border-black-300 flex justify-between items-center flex-wrap gap-5">
        <div className="text-white-500 flex gap-2">
            <p>Terms & Conditions</p>
            <p>|</p>
            <p>Privacy Policy</p>
        </div>
        <p className="text-white-500">
            Built with{' '}
            {technologies.map((tech, index) => (
                <span key={tech.name} className="whitespace-nowrap">
                    {index === technologies.length - 1 ? 'and ' : ''}{tech.name}{' '}
                    <img src={tech.icon} alt="" className="w-5 h-5 inline-block align-text-bottom" />
                    {index === technologies.length - 1 ? '.' : ', '}
                </span>
            ))}
        </p>
        <p className="text-white-500">© 2026 Somuna. All rights reserved.</p>
    </footer>
  )
}

export default Footer
