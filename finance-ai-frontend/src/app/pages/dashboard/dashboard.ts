import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DashboardService } from '../../services/dashboard.service';

import { Dashboard } from '../../models/dashboard';

@Component({

selector:'app-dashboard',

standalone:true,

imports:[CommonModule],

templateUrl:'./dashboard.html',

styleUrls:['./dashboard.css']

})

export class DashboardComponent implements OnInit{

  dashboard?:Dashboard;

loading=true;

days=[
'Mon',
'Tue',
'Wed',
'Thu',
'Fri',
'Sat',
'Sun'
];

constructor(private dashboardService:DashboardService){}

ngOnInit():void{

    this.dashboardService.getSummary().subscribe({

next:data=>{

this.dashboard=data;

this.loading=false;

},

error:err=>{

console.log(err);

this.loading=false;

}

});

}

}
