var IPCamera = (function () {
    'use strict';
    
    //Constructor
    function IPCamera( url )
    {
        Device.call( this );
        //public properties
        this.url = url;
    }

    IPCamera.prototype = Object.create( Device.prototype );
    IPCamera.prototype.constructor = IPCamera;

    return IPCamera;
})();

