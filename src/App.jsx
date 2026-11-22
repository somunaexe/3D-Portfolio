import Navbar from './sections/Navbar'
import Hero from './sections/Hero'
import About from './sections/About'
import Projects from './sections/Projects'
import Reviews from './sections/Reviews'
import Contact from './sections/Contact'
import Footer from './sections/Footer'
import Experience from './sections/Experience'
import ChatWidget from './components/ChatWidget'
import { isChatConfigured } from './lib/chatClient'
const App = () => {
  return (
    <main className='max-w-7xl mx-auto'>
      <Navbar />
      <Hero />
      <About />
      <Projects />
      <Reviews />
      <Experience />
      <Contact />
      <Footer />
      {isChatConfigured && <ChatWidget />}
    </main>
  )
}

export default App