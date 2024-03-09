var Watertank = (function() {
    'use strict';

    //Constructor
    function Watertank( mqtt_publish_topic, mqtt_subscribe_topic, filterById, idFilterValue, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
        this.filterById = filterById;
        this.idFilterValue = idFilterValue;
        this.watertank = { state: "unavailable", enabled: true };
    }

    Watertank.prototype = Object.create( MqttDevice.prototype );
    Watertank.prototype.constructor = Watertank;

    Watertank.prototype.update = function( topic, message )
    {
        const watertankList = JSON.parse(message)
        // console.log(watertankList);
        if(this.filterById)
        {
            console.log("will filter by id: '" + this.idFilterValue + "'");
            let wt = watertankList.filter(w => w.id === this.idFilterValue)
            if(wt != null && wt != undefined && wt[0] != null && wt[0] != undefined)
            {
                console.log("Found water tank " + this.idFilterValue + ": ", wt[0]);
                let wt_aux = wt[0];
                wt_aux.state = _determineWaterTankState(wt_aux);
                
                // add two gui related properties to the object
                if(!wt_aux.enabled)
                {
                    wt_aux['width_percentage'] = "0%";
                    wt_aux['str_percentage'] = "";
                }
                else if(wt_aux.state == 'sensor_error')
                {
                    wt_aux['width_percentage'] = "0%";
                    wt_aux['str_percentage'] = "";
                }
                else
                {
                    wt_aux['width_percentage'] = Math.round(wt_aux.percentage) + "%";
                    wt_aux['str_percentage'] = wt_aux.width_percentage;
                }

                // NOTE: ng-id uses guids for element id's. Guids may start with a number.
                // Such an element id will cause a crash if used in document.querySelector like
                // document.querySelector("#" + this.id + " .percent-bar") saying: 
                //
                // Connection lost: AMQJS0005E Internal error. Error Message: Failed to 
                // execute 'querySelector' on 'Document': '#3375f76e-520e-4469-8c3c-415b3e295467 
                // .percent-bar' is not a valid selector.
                //
                // So use getElementById and then querySelector.
                // see https://stackoverflow.com/a/37271406
                let watertankHtmlProgressBar = document.getElementById(this.id).querySelector( ".percent-bar");
                // console.log("watertankHtmlProgressBar: ", watertankHtmlProgressBar);
                if(watertankHtmlProgressBar)
                {
                    watertankHtmlProgressBar.style.width = wt_aux.width_percentage;
                }
                
                this.watertank = wt[0];
            }
        }
    }

    function _determineWaterTankState(watertank)
    {
        let state = "normal";

        if(watertank.invalid_sensor_measurement)
        {
            state = "sensor_error";
        }
        else if(watertank.percentage != null)
        {                  
            if(watertank.critical_level != null && watertank.percentage <= watertank.critical_level)
            {
                state = "critical";
            }
            else if(watertank.warning_level != null && watertank.percentage <= watertank.warning_level)
            {
                state = "warning";
            }
            else if(watertank.overflow_level != null && watertank.percentage >= watertank.overflow_level)
            {
                state = "overflow";
            }
        }

        console.log("state of watertank is " + state);
        return state;
    }

    return Watertank;
})();