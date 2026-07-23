export interface Dashboard{

    protectionScore:number;

    todayTransactions:number;

    blocked:number;

    safe:number;

    fraudDistribution:FraudDistribution[];

    weeklyTrend:number[];

    countries:string[];

    recentAlerts:Alert[];

}

export interface FraudDistribution{

    name:string;

    value:number;

    color:string;

}

export interface Alert{

    title:string;

    status:string;

    icon:string;

    color:string;

}