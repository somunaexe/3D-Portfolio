import { clientReviews } from "../constants"

const Clients = () => {
    const checkReviewLength = (reviewParam) => {
        const shortLength = 200
        const isLong = reviewParam.length > shortLength
        let slicedReview = (isLong) ? reviewParam.slice(0, shortLength) + '... ' : reviewParam
        return (
            <>
                {slicedReview} {isLong && <span className="hover:underline text-blue-500">read more</span>}
            </>
        );
    }

  return (
    <section className="c-space my-20" id="clients">
        <h3 className="head-text">Hear from My Clients</h3>
        <div className="client-container">
            {clientReviews.map(({id, name, review, img, position, link}) => (
                <div key={id} className="client-review">
                    <div>
                        <a href={link} target="_blank"><p className="text-white font-light justify-between">{checkReviewLength(review)}</p></a>
                        <div className="client-content">
                            <div className="flex gap-3">
                                <img src={img} alt={name} className="w-12 h-12 rounded-full" />
                                <div className="flex flex-col">
                                    <p className="font-semibold text-white-800">{name}</p>
                                    <p className="text-white-500 md:text-base text-sm">{position}</p>
                                </div>
                            </div>
                            <div className="flex self-end items-center gap-2">
                                {Array.from({ length: 5 }).map((_, index) => (
                                    <img key={index} src="/assets/star.png" alt="star" className="w-5 h-5" />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    </section>
  )
}

export default Clients