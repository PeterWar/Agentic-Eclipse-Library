"""Record completed negative experiments without changing the delivered PSB."""
from a4_sources import *

def main():
 solar=json.loads((O/'BRNO_SOLAR_T_R02_QA.json').read_text())
 moment=json.loads((O/'MOMENT_R02_BOUNDARY_QA.json').read_text())
 assert moment['input_integrity_PASS']
 save(O/'SOLAR_R02_DECISION.json',{
  'status':'NOT_PROMOTED_AS_A_PACKAGE','candidates':['filters_solar_T_E2','filters_solar_T_E3'],
  'domain':'physical positive support outside fixed projected solar disk; no fitted margin',
  'newly_excluded_pixels':2783,'all_newly_excluded_inside_photo_Moon':True,
  'reason':'Some marked contrasts decrease, but broad E3 bands and inner Brno morphology regress. No evidence of a qualifying package; solar radius does not establish the complete contamination footprint.',
  'Brno800_band13_30_inner_delta_vs_R01':{'WOW':-.00274,'bilateral':-.00493,'MGN':-.04277,'01':-.00286,'04':.00003,'05':-.02802,'06':-.08578},
  'sources':['BRNO_SOLAR_T_R02_QA.json','marks246_solar_R02/METRICS.json','solar_peak_trace_R02/TRACE.json'],
  'analytic_solar_controls_not_run':True,'source_radiance_unchanged':True,'PSB_unchanged':True})
 save(O/'MOMENT_R02_DECISION.json',{
  'status':'NOT_PROMOTED','candidates':['filters_moment_E3'],
  'method':'Discrete Gaussian mean from quadratic local moments on observed domain; fixed coefficients, no ridge or clipping; weighted original postprocess preserved',
  'positive_scopes':['quadratic null','hidden-value invariance','original full-stencil Gaussian equality','bounded condition number','one fixed white-noise control'],
  'transfer_failures_old_new':{'01':[15,12],'04':[19,9],'05':[14,12],'06':[20,14]},
  'reason':'Fewer failed transfer cells conceal increased failure severity. The active 04 reverses some injected detail near the boundary; other operators introduce new failed cells.',
  '04_examples':[
   'wavelength18 radial0..2 gain .719 -> -.0108',
   'wavelength18 oblique0..2 gain .642 -> -.108',
   'wavelength18 radial2..4 gain .791 -> .195',
   'wavelength18 oblique2..4 gain .777 -> .113',
   'wavelength70 radial4..8 gain .491 -> 1.504'],
  'independent_review':'qa_regeneration; root viewed E3_comparison.png; no global improvement claim',
  'sources':['MOMENT_R02_BOUNDARY_QA.json','BRNO_MOMENT_R02_QA.json','moment_E3_R02/NULL_QA.json','moment_E3_R02/WHITE_NOISE_QA.json','marks246_moment_R02/METRICS.json'],
  'control_interpretation':'Hidden injections combine visible-signal retention with an unobservable continuation hypothesis. Existing failures remain recorded; null success cannot erase them.',
  'production_dispatch_fix':'moment_E3_R02/DISPATCH_CLARIFICATION.json; initial failed attempt preserved',
  'source_radiance_unchanged':True,'PSB_unchanged':True})
 save(O/'TEMPORAL_CALIBRATION_R02.json',{
  'status':'ALREADY_PRESENT_NO_EXTRA_GAIN_APPLIED',
  'chain':['RAW dark/flat/exposure/WB','F2.2 coherence factor k_i','V36 per-frame RGB offsets and smooth spatial phi','a9 registered N and W contain these calibrations'],
  'k_examples':{'2960':.9079961,'2961':.8969768,'3024':.9541050,'3025':.9378850},
  'source_paths':['2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/frozen_code/comu.py','2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/frozen_code/f2.py','2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v29_sources_dependencies/grid.py','2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v36_rgb_dependencies/b1.py','3-RECERCA/tools/v85_regeneracio_20260922/a9_limb_frames.py'],
  'implication':'The residual between fixed early/late pairs is after existing calibration; do not interpret it as missing temporal transparency correction.',
  'independent_readonly_review':'filter_sources','heldout_N_not_read':True})
 save(O/'WORKING_STATE_R02.json',{
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'round':'R02',
  'status':'ACTIVE_SOURCE_DIAGNOSTIC_NO_PSB_CHANGE','delivery_still':'1-PHOTOSHOP/V85.psb (R01 bounded)',
  'claim':CID+' HELD','completed':['physicalD/T domains','solarT domain','quadratic moment E3 nulls/noise/knowntruth/marks/Brno/visual','train-only B(D) component contrast','temporal calibration audit'],
  'not_promoted':['physicalD','physicalT package','solarT package','quadratic moment E3'],
  'active':'read-only causal decomposition of B(D) effect at component1; root sole writer',
  'next':['identify source-level cause separately from filter padding','correct memory note and skill receipts','no unsupported all-artifacts-resolved claim'],
  'goal_complete':False})
 print('R02_NEGATIVES_RECORDED')

if __name__=='__main__':guard();main()
