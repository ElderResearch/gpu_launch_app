function roundDay(timestamp){
    timestamp.setHours(0);
    timestamp.setMinutes(0);
    timestamp.setSeconds(0);
    timestamp.setMilliseconds(0);
    return timestamp;
};

// Date range start date
$('#start-date').datepicker({
    weekStart: 1,
    daysOfWeekHighlighted: "6,0",
    autoclose: true,
    todayHighlight: true,
    format: "mm/dd/yyyy",
    startDate: "03-02-2019",
    endDate: roundDay(new Date())
  }
  ).datepicker(
    'setUTCDate', roundDay(new Date(new Date().setMonth(new Date().getMonth()-1)))
  ).on('hide', function(e) {
    // update the minimum selectable end-date
    $('#end-date').datepicker('setStartDate', e.date);
    // ensure that start-date >= end-date
    if ($('#end-date').datepicker('getDate') < e.date) {
      $('#end-date').datepicker('setUTCDate', new Date(new Date(e.date).setDate(new Date(e.date).getDate()+1)));
    }
    // shift focus to end-date when start-date is closed
    $('#end-date').datepicker('show');
  });

$('#end-date').datepicker({
    weekStart: 1,
    daysOfWeekHighlighted: "6,0",
    autoclose: true,
    todayHighlight: true,
    format: "mm/dd/yyyy",
    startDate: "03-02-2019",
    endDate: new Date(new Date().setDate(new Date().getDate()+1))
  }
  ).datepicker(
    'setUTCDate', new Date()
  ).on('hide', function(e) {
    // send the data query and update charts
    let startDate = $('#start-date').datepicker('getUTCDate');
    let endDate = $('#end-date').datepicker('getUTCDate');
    queryActivityLog(startDate.toISOString(), endDate.toISOString());
  });

function queryActivityLog(startDate, endDate) {
  let url = new URL('/data', window.location.origin);
  let params = {start_date: startDate, end_date: endDate};
  url.search = new URLSearchParams(params);

  return fetch(url)
  .then(response=>{return response.json()})
  .then(json=>{

    // update total containers key metric
    $('#launched-containers-metric').html(json.length);

    // update total runtime hours key metric
    $('#runtime-hours-metric').html(
      Math.round(d3.sum(json, d => d.runtime)));

    // update gpu utilization metric
    $('#gpu-utilization-metric').html(
      Math.round(
        d3.sum(json, d => d.gpu_hours) / d3.sum(json, d => d.runtime) * 100) + "%");

    // update AWS savings metric
    let awsCost = 3.06
    $('#aws-savings-metric').html(
      "$" + (d3.sum(json, d => d.gpu_hours) * awsCost).toFixed(2)
    )
    // update runtime bar graph
    resetChart(runtimeBar);
    (d3.nest()
    .key(d => d.username)
    .rollup(v => d3.sum(v, d => d.runtime))
    .entries(json))
    .sort((a,b) => {return b.value - a.value;})
    .map(o => addData(runtimeBar, o.key, o.value.toFixed(2)));

    // update gpu usage pie graph
    resetChart(gpuUsagePie);
    (d3.nest()
    .key(d => d.username)
    .rollup(v => d3.sum(v, d => d.gpu_hours))
    .entries(json))
    .filter(d => {return d.value > 0;})
    .sort((a,b) => {return b.value - a.value;})
    .map(o => addData(gpuUsagePie, o.key, o.value.toFixed(2)));

    // update gpu utilization bar
    resetChart(utilizationBar);
    (d3.nest()
    .key(d => d.username)
    .rollup(v => {return {
      gpu_hours: d3.sum(v, d => d.gpu_hours),
      total_hours: d3.sum(v, d => d.runtime)}})
    .entries(json)).map(d => {return {
      key: d.key,
      value: d.value.gpu_hours / d.value.total_hours * 100}})
    .filter(d => { return d.value > 0; })
    .sort((a,b) => { return b.value - a.value; })
    .map(o =>{addData(utilizationBar, o.key, o.value.toFixed(2))});

    // update containers bar
    resetChart(containersBar);
    var images = json.reduce((arr, val) => {
        arr.push(val.image_type); return arr;}, [])
      .filter((value,index,self) => {return self.indexOf(value) === index;})
      .sort();
    
    var users = d3.nest()
    .key(d=>d.username)
    .rollup(d=>d.length)
    .entries(json)
    .sort((a,b)=>{return b.value - a.value})
    .reduce((arr,d)=>(arr.push(d.key),arr),[]);
    
    var intermediate = (d3.nest()
    .key(d => d.username)
    .entries(json))
    .sort((a,b)=>{return users.indexOf(a.key) - users.indexOf(b.key)})
    .map(function(d) {
        var counts = d3.nest()
             .key(o => o.image_type)
             .rollup(o => o.length)
             .map(d.values);
        return {key: d.key,
          values: images.reduce((obj,img) => (
            obj[img] = counts.get(img) || 0, obj), {})
          };
        })
    
    containersBar.data.labels = users;

    containersBar.data.datasets = images.map(img=>{
      return {
        label: img,
        data: intermediate.reduce((arr,usr)=>(arr.push(usr.values[img]),arr),[])}});
    
    containersBar.update();

})
};

feather.replace();

var chartColors = {
  red: 'rgb(230, 25, 75)',
  blue: 'rgb(0, 130, 200)',
  green: 'rgb(60, 180, 75)',
  yellow: 'rgb(255, 225, 25)',
  orange: 'rgb(245, 130, 48)',
  cyan: 'rgb(70, 240, 240)',
  magenta: 'rgb(240, 50, 230)',
  pink: 'rgb(250, 190, 190)',
  teal: 'rgb(0, 128, 128)',
  lavender: 'rgb(230, 190, 255)',
  brown: 'rgb(170, 110, 40)',
  maroon: 'rgb(128, 0, 0)',
  navy: 'rgb(0, 0, 128)',
	grey: 'rgb(128, 128, 128)'
};

function resetChart(chart) {
  chart.data.labels = [];
  chart.data.datasets.forEach((dataset) => {
      dataset.data = [];
  });
  chart.update();
};

function addData(chart, label, data) {
    chart.data.labels.push(label);
    chart.data.datasets.forEach((dataset) => {
        dataset.data.push(data);
    });
    chart.update();
};

// container timeline
var ctx = document.getElementById("container-timeline").getContext('2d');
var timeline = new Chart(ctx, {
  type: 'line',
  data: {
    datasets: [
      {
        label: 'Python',
        backgroundColor: chartColors.blue,
        borderColor: chartColors.blue,
        fill: false,
        borderWidth : 40,
        pointRadius : 0,
        data: [
          {
            x: 0,
            y: 'andrew'
          }, 
          {
            x: 3,
            y: 'andrew'
          },
        ]
      },
      {
        backgroundColor: chartColors.green,
        borderColor: chartColors.green,
        fill: false,
        borderWidth : 40,
        pointRadius : 0,
        data: [
          {
            x: 4,
            y: 'andrew'
          }, 
          {
            x: 6,
            y: 'andrew'
          }
        ]
      },
      {
        backgroundColor: chartColors.red,
        borderColor: chartColors.red,
        fill: false,
        borderWidth : 40,
        pointRadius : 0,
        data: [
          {
            x: 3,
            y: 'carl'
          }, 
          {
            x: 5,
            y: 'carl'
          }
        ]
      },
      {
        backgroundColor: chartColors.blue,
        borderColor: chartColors.blue,
        fill: false,
        borderWidth : 40,
        pointRadius : 0,
        data: [
          {
            x: 5,
            y: 'carlos'
          }, {
            x: 10,
            y: 'carlos'
          }
        ]
      },
      {
        backgroundColor: chartColors.red,
        borderColor: chartColors.red,
        fill: false,
        borderWidth : 40,
        pointRadius : 0,
        data: [
          {
            x: 10,
            y: 'ian'
          }, {
            x: 13,
            y: 'ian'
          }
        ]
      }
    ]
  },
  options: {
    tooltips: {
      mode: 'dataset',
      intersect: true
    },
    legend: {
      display : false
    },
    scales: {
      xAxes: [{
        type: 'linear',
        position: 'bottom',
        ticks : {
          beginAtzero :true,
          stepSize : 1
        }
      }],
      yAxes : [{
        offset: true,
        type: 'category',
        labels: ['andrew', 'carl', 'carlos', 'ian']
      }]
    }
  }
});

// containers bar
var ctx = document.getElementById("containers-bar").getContext('2d');
var containersBar = new Chart(ctx, {
    type: 'bar',
    options: {
      title: {
        display: false,
      },
      legend: {
        display: false
      },
      tooltips: {
        mode: 'index',
        intersect: false
      },
      responsive: true,
      scales: {
        xAxes: [{
          stacked: true,
        }],
        yAxes: [{
          stacked: true
        }]
      }
    },
    plugins: [{
      beforeUpdate: function(ctx){
        for (var i = 0; i < ctx.config.data.datasets.length; i++) {
          ctx.config.data.datasets[i].backgroundColor = Object.values(chartColors)[i];
        }
      }
    },]
  });

// runtime bar
var ctx = document.getElementById("runtime-bar").getContext('2d');
var runtimeBar = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        backgroundColor: chartColors.blue,
        data: []
      }]
    },
    options: {
      title: {
        display: false,
      },
      legend: {
        display: false,
      },
      tooltips: {
        mode: 'index',
        intersect: false
      },
      responsive: true,
    }
  });

// gpu usage pie
var ctx = document.getElementById("gpu-usage-pie");
var gpuUsagePie = new Chart(ctx, {
  type: 'pie',
  data: {
    labels: [],
    datasets: [{
      backgroundColor: Object.values(chartColors),
      data: []
    }]
  },
  options: {
    legend: {
      display: true,
      position: 'right'
    }
  }
});

// utilization bar
var ctx = document.getElementById("utilization-bar");
var utilizationBar = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: [],
    datasets: [{
      backgroundColor: chartColors.blue,
      data: []
    }]
  },
  options: {
    title: {
      display: false,
    },
    legend: {
      display: false,
    },
    tooltips: {
      mode: 'index',
      intersect: false
    },
    responsive: true,
  }
});
