var Door1 = (function () {
    'use strict';
    
    //Constructor
    function IPCameraPanTilt( baseUrl, videostream, right, left, up, down, stop )
    {
        Device.call( this );
        //public properties
        this.baseUrl = baseUrl; 
        this.videostream = videostream; 
        this.right = right; 
        this.left = left; 
        this.up = up; 
        this.down = down; 
        this.stop = stop;        
    }

    IPCameraPanTilt.prototype = Object.create( Device.prototype );
    IPCameraPanTilt.prototype.constructor = IPCameraPanTilt;

    function videoUrl() { return baseUrl + videostream ; }
    function rightUrl() { return baseUrl + right ; }
    function leftUrl() { return baseUrl + left ; }
    function upUrl() { return baseUrl + up ; }
    function downUrl() { return baseUrl + down ; }
    function stopUrl() { return baseUrl + stop ; }

    return IPCameraPanTilt;
})();
