import { useRef, useState } from 'react'
// import emailjs from '@emailjs/browser'

const Contact = () => {
    const formRef = useRef();
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false)
    const [form, setForm] = useState({
        name: '',
        email: '',
        message: '',
    })

    const handleChange = ({ target: { name, value }}) => {
        setForm({ ...form, [name]: value })
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const enquiry = {
            fullName: form.name,
            email: form.email,
            message: form.message,
        }

        const response = await fetch("https://db4zdyqcd6.execute-api.eu-north-1.amazonaws.com/default/",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(enquiry),
            }
        );

        const data = await response.json();
        setMessage(data.message || "Message sent successfully!");

        // reset form fields
        setForm({
        name: "",
        email: "",
        message: "",
        });

        setLoading(false);
    }

    // const handleSubmit = async (e) => {
    //     e.preventDefault();
    //     setLoading(true)

    //     try {
    //         await emailjs.send(
    //             'service_3wzb08p',
    //             'template_5zwtiy8', 
    //             {
    //                 from_name: form.name,
    //                 to_name: 'Somuna',
    //                 from_email: form.email,
    //                 to_email: 'somunanzenwa@gmail.com',
    //                 message: form.message,
    //             },
    //             'YnXxUAX9UmdXN5MoZ'
    //         )

    //         setLoading(false)
    //         alert('Message sent successfully!')

    //         setForm({
    //             name: '',
    //             email: '',
    //             message: '',
    //         })
    //     } catch (error) {
    //         setLoading(false)
    //         console.log(error)
    //         alert('Something went wrong!')
    //     }
    // }
  return (
    <section className="c-space my-20" id="contact">
        <div className="relative min-h-screen flex items-center justify-center flex-col">
            <img src="/assets/terminal.png" alt="terminal background" className="absolute inset-0 min-h-screen"/>
            
            <div className="contact-container">
                <h3 className="head-text">Let&apos;s talk</h3>
                <p className="text-lg text-white-600 mt-3">
                    Whether you&apos;re looking to build a new website, improve your existing platform, or bring a unique project to life, I&apos;m here to help.
                </p>
                {message && (
                    <p className="text-lg text-green-500 mt-3 font-semibold">{message}</p>
                )}
                <form ref={formRef} onSubmit={handleSubmit} className="mt-12 flex flex-col space-y-7">
                    <label className="space-y-3">
                        <span className="field-label">Full Name</span>
                        <input type="text" name="name" value={form.name} onChange={handleChange} required className="field-input" placeholder="ex., John Doe"/>
                    </label>

                    <label className="space-y-3">
                        <span className="field-label">Email address</span>
                        <input type="email" name="email" value={form.email} onChange={handleChange} required className="field-input" placeholder="ex., johndoe@gmail.com"/>
                    </label>

                    <label className="space-y-3">
                        <span className="field-label">Your message</span>
                        <textarea name="message" value={form.message} onChange={handleChange} required rows={5} className="field-input" placeholder="Hi, I wanna give you a job... 🙂"/>
                    </label>

                    <button className="field-btn" type="submit" disabled={loading}>
                        {loading ? 'Sending...' : 'Send message'}
                        <img src="/assets/arrow-up.png" alt="arrow-up" className="field-btn_arrow"/>
                    </button>
                </form>
            </div>
        </div>
    </section>
  )
}

export default Contact