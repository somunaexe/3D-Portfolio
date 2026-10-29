import { useState } from "react"
import { navLinks } from "../constants/index.js"
import Links from "../components/Links.jsx"
import ThemeSlider from "../components/ThemeSlider.jsx"
const NavItems = () => {
  return (
    <ul className="nav-ul">
        {navLinks.map(({id, href, name }) => (
            <li key={id} className="nav-li">
                <a href={href} className="nav-li_a"
                >{name}</a>
            </li>
        ))}
    </ul>
  )
}

const Navbar = () => {
    const [isOpen, setIsOpen] = useState(false)
    const toggleMenu = () => setIsOpen((prevIsOpen) => !prevIsOpen)

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[rgb(var(--navbar-bg))] border-b border-[color:var(--navbar-border)]">
        <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center py-5 mx-auto c-space">
                <div className="flex items-center gap-5">
                    <a
                        href="/"
                        className="flex flex-col leading-tight text-white-600 hover:text-white-900 transition-colors">
                        <span className="font-bold text-xl">SuperSomu</span>
                        <span className="text-xs">Artificial Intelligence MSc Graduate</span>
                    </a>
                    <Links />
                </div>
                <button
                onClick={toggleMenu}
                className="
                text-white-600
                hover:text-white-900
                focus:outline-none
                sm:hidden
                flex"
                aria-label="Toggle menu">
                    <img 
                    src={isOpen ? "/assets/close.svg" : "/assets/menu.svg"} 
                    alt="toggle" 
                    className="w-6 h-6 themed-icon"/>
                </button>
                <ThemeSlider className="hidden lg:flex" />
                <nav className="sm:flex hidden">
                    <NavItems />
                </nav>
            </div>
            <ThemeSlider className="lg:hidden justify-center pb-3 -mt-1" />
        </div>
        <div className={`nav-sidebar ${isOpen ? 'max-h-screen' : 'max-h-0'}`}>
            <nav className="p-5">
                <NavItems />
            </nav>
        </div>
    </header>
  )
}

export default Navbar