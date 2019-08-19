// Date range start date
$('#start-date').datepicker({
    weekStart: 1,
    daysOfWeekHighlighted: "6,0",
    autoclose: true,
    todayHighlight: true,
    format: "mm/dd/yyyy",
    startDate: "03-02-2019",
    endDate: new Date()
  }
  ).datepicker(
    'setUTCDate', new Date(new Date().setMonth(new Date().getMonth()-1))
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
      Math.round(d3.sum(json, d => {return d.runtime})));

    // update gpu utilization metric
    $('#gpu-utilization-metric').html(
      Math.round(
        d3.sum(json, d => {return d.gpu_hours}) / d3.sum(json, d => {return d.runtime}) * 100) + "%");

    // update AWS savings metric
    let awsCost = 3.06
    $('#aws-savings-metric').html(
      "$" + (d3.sum(json, d => {return d.gpu_hours}) * awsCost).toFixed(2)
    )
    // update runtime bar graph
    resetChart(runtimeBar);
    (d3.nest()
    .key(function(d) {return d.username})
    .rollup(function(v) {return d3.sum(v, function(d) {return d.runtime})})
    .entries(json))
    .sort((a,b)=>{return b.value - a.value})
    .map(obj=>{addData(runtimeBar, obj.key, obj.value.toFixed(2))});

    // update gpu usage pie graph
    resetChart(gpuUsagePie);
    (d3.nest()
    .key(function(d) {return d.username})
    .rollup(function(v) {return d3.sum(v, function(d) {return d.gpu_hours})})
    .entries(json))
    .filter(d=>{ return d.value > 0; })
    .sort((a,b)=>{return b.value - a.value})
    .map(obj=>{addData(gpuUsagePie, obj.key, obj.value.toFixed(2))});

    // update gpu utilization bar
    resetChart(utilizationBar);
    (d3.nest()
    .key(function(d) {return d.username})
    .rollup(function(v) {return {
      gpu_hours: d3.sum(v, function(d) {return d.gpu_hours}),
      total_hours: d3.sum(v, function(d) {return d.runtime})
    }
    })
    .entries(json)).map(d=>{return {
      key: d.key,
      value: d.value.gpu_hours / d.value.total_hours * 100
    }})
    .filter(d=>{ return d.value > 0; })
    .sort((a,b)=>{ return b.value - a.value; })
    .map(obj=>{addData(utilizationBar, obj.key, obj.value.toFixed(2))});
  })
};

feather.replace();

var chartColors = {
	red: 'rgb(230, 25, 75)',
  green: 'rgb(60, 180, 75)',
  yellow: 'rgb(255, 225, 25)',
  blue: 'rgb(0, 130, 200)',
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
var timeline = new Chart(document.getElementById("container-timeline"), {
  type: 'line',
  data: {
    labels: [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday'
    ],
    datasets: [{
      data: [
        15339,
        21345,
        18483,
        24003,
        23489,
        24092,
        12034
      ],
      lineTension: 0,
      backgroundColor: 'transparent',
      borderColor: '#007bff',
      borderWidth: 4,
      pointBackgroundColor: '#007bff'
    }]
  },
  options: {
    scales: {
      yAxes: [{
        ticks: {
          beginAtZero: false
        }
      }]
    },
    legend: {
      display: false
    }
  }
});


// containers bar
var containersBarData = {
  labels: [
    'astewart',
    'chase',
    'imyjer',
    'tbradberry',
    'cblancarte',
    'jgongora',
    'sballerini'],
  datasets: [{
    label: 'Python',
    backgroundColor: chartColors.red,
    data: [2, 5, 3, 7, 4, 2, 5]
  }, {
    label: 'Python+R',
    backgroundColor: chartColors.blue,
    data: [4, 5, 2, 4, 7, 5, 6]
  }, {
    label: 'Aegir',
    backgroundColor: chartColors.green,
    data: [7, 4, 2, 1, 2, 0, 3]
  }]
};

var containersBar = new Chart(document.getElementById("containers-bar"), {
    type: 'bar',
    data: containersBarData,
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
    }
  });

// runtime bar
var runtimeBar = new Chart(document.getElementById("runtime-bar"), {
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
      scales: {
        xAxes: [{
          stacked: true,
        }],
        yAxes: [{
          stacked: true
        }]
      }
    }
  });


// gpu usage pie
var gpuUsagePie = new Chart(document.getElementById("gpu-usage-pie"), {
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
var utilizationBar = new Chart(document.getElementById("utilization-bar"), {
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
    scales: {
      xAxes: [{
        stacked: true,
      }],
      yAxes: [{
        stacked: true
      }]
    }
  }
});
