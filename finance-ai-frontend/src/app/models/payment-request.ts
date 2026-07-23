export interface PaymentRequest{

    beneficiary_name:string;

    beneficiary_account:string;

    new_beneficiary:boolean;

    transaction_amount:number;

    transaction_type:string;

    transaction_time:string;

    transaction_location:string;

    device_type:string;

    previous_transactions_count:number;

}