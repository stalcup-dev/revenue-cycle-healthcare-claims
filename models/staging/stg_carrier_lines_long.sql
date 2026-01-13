-- stg_carrier_lines_long.sql
-- Wide-to-long transformation for carrier lines

with raw_union as (
    select * from rcm.raw_carrier_1a
    union all
    select * from rcm.raw_carrier_1b
),
long_lines as (
    select
        DESYNPUF_ID as desynpuf_id,
        CLM_ID as clm_id,
        line_num,
        allowed_incl_patient as allowed_amt,
        bene_deductible as deductible_amt,
        coinsurance_amt,
        nch_pmt_amt,
        coalesce(primary_payer_paid_amt, 0) as primary_payer_paid_amt,
        line_prcsg_ind_cd,
        hcpcs_cd,
        SAFE.PARSE_DATE('%Y%m%d', CAST(NULLIF(CLM_FROM_DT, 0) AS STRING)) as svc_from_dt,
        SAFE.PARSE_DATE('%Y%m%d', CAST(NULLIF(CLM_THRU_DT, 0) AS STRING)) as svc_thru_dt,
        COALESCE(
            SAFE.PARSE_DATE('%Y%m%d', CAST(NULLIF(CLM_THRU_DT, 0) AS STRING)),
            SAFE.PARSE_DATE('%Y%m%d', CAST(NULLIF(CLM_FROM_DT, 0) AS STRING))
        ) as svc_dt
    from raw_union,
    unnest([
        struct(1 as line_num,
            LINE_ALOWD_CHRG_AMT_1 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_1 as bene_deductible,
            LINE_COINSRNC_AMT_1 as coinsurance_amt,
            LINE_NCH_PMT_AMT_1 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_1, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_1 as line_prcsg_ind_cd,
            HCPCS_CD_1 as hcpcs_cd
        ),
        struct(2 as line_num,
            LINE_ALOWD_CHRG_AMT_2 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_2 as bene_deductible,
            LINE_COINSRNC_AMT_2 as coinsurance_amt,
            LINE_NCH_PMT_AMT_2 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_2, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_2 as line_prcsg_ind_cd,
            HCPCS_CD_2 as hcpcs_cd
        ),
        struct(3 as line_num,
            LINE_ALOWD_CHRG_AMT_3 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_3 as bene_deductible,
            LINE_COINSRNC_AMT_3 as coinsurance_amt,
            LINE_NCH_PMT_AMT_3 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_3, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_3 as line_prcsg_ind_cd,
            HCPCS_CD_3 as hcpcs_cd
        ),
        struct(4 as line_num,
            LINE_ALOWD_CHRG_AMT_4 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_4 as bene_deductible,
            LINE_COINSRNC_AMT_4 as coinsurance_amt,
            LINE_NCH_PMT_AMT_4 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_4, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_4 as line_prcsg_ind_cd,
            HCPCS_CD_4 as hcpcs_cd
        ),
        struct(5 as line_num,
            LINE_ALOWD_CHRG_AMT_5 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_5 as bene_deductible,
            LINE_COINSRNC_AMT_5 as coinsurance_amt,
            LINE_NCH_PMT_AMT_5 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_5, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_5 as line_prcsg_ind_cd,
            HCPCS_CD_5 as hcpcs_cd
        ),
        struct(6 as line_num,
            LINE_ALOWD_CHRG_AMT_6 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_6 as bene_deductible,
            LINE_COINSRNC_AMT_6 as coinsurance_amt,
            LINE_NCH_PMT_AMT_6 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_6, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_6 as line_prcsg_ind_cd,
            HCPCS_CD_6 as hcpcs_cd
        ),
        struct(7 as line_num,
            LINE_ALOWD_CHRG_AMT_7 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_7 as bene_deductible,
            LINE_COINSRNC_AMT_7 as coinsurance_amt,
            LINE_NCH_PMT_AMT_7 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_7, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_7 as line_prcsg_ind_cd,
            HCPCS_CD_7 as hcpcs_cd
        ),
        struct(8 as line_num,
            LINE_ALOWD_CHRG_AMT_8 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_8 as bene_deductible,
            LINE_COINSRNC_AMT_8 as coinsurance_amt,
            LINE_NCH_PMT_AMT_8 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_8, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_8 as line_prcsg_ind_cd,
            HCPCS_CD_8 as hcpcs_cd
        ),
        struct(9 as line_num,
            LINE_ALOWD_CHRG_AMT_9 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_9 as bene_deductible,
            LINE_COINSRNC_AMT_9 as coinsurance_amt,
            LINE_NCH_PMT_AMT_9 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_9, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_9 as line_prcsg_ind_cd,
            HCPCS_CD_9 as hcpcs_cd
        ),
        struct(10 as line_num,
            LINE_ALOWD_CHRG_AMT_10 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_10 as bene_deductible,
            LINE_COINSRNC_AMT_10 as coinsurance_amt,
            LINE_NCH_PMT_AMT_10 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_10, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_10 as line_prcsg_ind_cd,
            HCPCS_CD_10 as hcpcs_cd
        ),
        struct(11 as line_num,
            LINE_ALOWD_CHRG_AMT_11 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_11 as bene_deductible,
            LINE_COINSRNC_AMT_11 as coinsurance_amt,
            LINE_NCH_PMT_AMT_11 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_11, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_11 as line_prcsg_ind_cd,
            HCPCS_CD_11 as hcpcs_cd
        ),
        struct(12 as line_num,
            LINE_ALOWD_CHRG_AMT_12 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_12 as bene_deductible,
            LINE_COINSRNC_AMT_12 as coinsurance_amt,
            LINE_NCH_PMT_AMT_12 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_12, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_12 as line_prcsg_ind_cd,
            HCPCS_CD_12 as hcpcs_cd
        ),
        struct(13 as line_num,
            LINE_ALOWD_CHRG_AMT_13 as allowed_incl_patient,
            LINE_BENE_PTB_DDCTBL_AMT_13 as bene_deductible,
            LINE_COINSRNC_AMT_13 as coinsurance_amt,
            LINE_NCH_PMT_AMT_13 as nch_pmt_amt,
            ifnull(LINE_BENE_PRMRY_PYR_PD_AMT_13, 0) as primary_payer_paid_amt,
            LINE_PRCSG_IND_CD_13 as line_prcsg_ind_cd,
            HCPCS_CD_13 as hcpcs_cd
        )
    ]) as line
)

select
    desynpuf_id,
    clm_id,
    line_num,
    svc_dt,
    hcpcs_cd,
    line_prcsg_ind_cd,
    allowed_amt,
    deductible_amt,
    coinsurance_amt,
    nch_pmt_amt,
    primary_payer_paid_amt
from long_lines
where hcpcs_cd is not null
   or allowed_amt > 0
   or nch_pmt_amt > 0
   or deductible_amt > 0
   or coinsurance_amt > 0
   or primary_payer_paid_amt > 0
