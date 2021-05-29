function splitscroll() {
    const controller = new ScrollMagic.Controller()
    if (screen.width > 768) {
        // Songs
        new ScrollMagic.Scene({
                duration: document.querySelector("#top_tracks").clientHeight-window.innerHeight*0.6,
                triggerElement: '#top_tracks_title',
                triggerHook: 0
            })
            .setPin('#top_tracks_title', {pushFollowers: false})
            .addTo(controller)
        // Year
        new ScrollMagic.Scene({
            duration:  document.querySelector("#top_year").clientHeight,
            triggerElement: '#top_year',
            triggerHook: 0
        })
        .setPin('#top_year', {pushFollowers: false})
        .addTo(controller)            
     
        // Albums
        new ScrollMagic.Scene({
            duration: document.querySelector("#top_albums").clientHeight-window.innerHeight*0.6,
            triggerElement: '#top_albums_title',
            triggerHook: 0
        })
        .setPin('#top_albums_title', {pushFollowers: false})
        .addTo(controller)
        // Artists
        new ScrollMagic.Scene({
            duration: document.querySelector("#top_artists").clientHeight-window.innerHeight*0.6,
            triggerElement: '#top_artists_title',
            triggerHook: 0
        })
        .setPin('#top_artists_title', {pushFollowers: false})
        .addTo(controller)
    }

}

splitscroll()
