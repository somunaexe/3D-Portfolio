import { Canvas } from "@react-three/fiber"
import { PerspectiveCamera } from "@react-three/drei"
import HackerRoom from "../components/HackerRoom"
import { Suspense } from "react"
import CanvasLoader from "../components/CanvasLoader"
import { Leva, useControls } from "leva"
const Hero = () => {
    const co = useControls('HackerRoom', {
        positionX: {
            value: 2.5,
            min: -10,
            max: 10
        },
        positionY: {
            value: 2.5,
            min: -10,
            max: 10
        },
        positionZ: {
            value: 2.5,
            min: -10,
            max: 10
        }
    })

  return (
    <section className="min-h-screen w-full flex flex-col relative">
        <div className="w-full mx-auto flex flex-col sm:mt-36 mt-20 c-space gap-3">
            <p className="sm:text-3xl text-2xl font-medium text-white text-center font-generalsans">Hi, I am Somuna.<span className="waving-hand">👋🏽</span></p>
            <p className="hero_tag text-gray_gradient">Building Software</p>
        </div>
        
        <div className="w-full h-full absolute inset-0">
        <Leva />
            <Canvas className="w-full h-full">
                <Suspense fallback={<CanvasLoader />}>
                    <PerspectiveCamera makeDefault position={[0, 0, 0]}/>
                    <HackerRoom 
                        scale={[co.positionX, co.positionY, co.positionZ]} 
                        position={[0, 0, 0]} 
                        rotation={[0, -Math.PI / 2, 0]} 
                    />
                    <ambientLight intensity={1} />
                    <directionalLight position={[10, 10, 10]} intensity={0.5} />

                </Suspense>
            </Canvas>
        </div>
    </section>
  )
}

export default Hero