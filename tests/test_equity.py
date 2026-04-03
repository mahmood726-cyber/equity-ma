"""
Selenium test suite for EquityMA — Equity-Stratified Meta-Analysis Tool.
Tests statistical functions, study management, PRISMA-E checklist, CSV import,
dimension analysis, examples, and export.
"""
import sys, io, os, unittest, time, math
if not hasattr(sys.stdout, '_pytest_capture'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

HTML = 'file:///' + os.path.abspath(r'C:\Models\EquityMA\equity-ma.html').replace('\\', '/')


class TestEquityMA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-gpu')
        cls.drv = webdriver.Chrome(options=opts)
        cls.drv.get(HTML)
        time.sleep(1)
        # Clear localStorage to start fresh
        cls.drv.execute_script("localStorage.clear();")
        cls.drv.refresh()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.drv.quit()

    def js(self, script):
        return self.drv.execute_script(script)

    # ---------------------------------------------------------------
    # 1. Constants loaded correctly
    # ---------------------------------------------------------------
    def test_01_dims_loaded(self):
        """DIMS array should have 11 PROGRESS-Plus dimensions"""
        count = self.js("return DIMS.length;")
        self.assertEqual(count, 11)

    def test_02_prisma_items_loaded(self):
        """PRISMA_ITEMS should have 27 checklist items"""
        count = self.js("return PRISMA_ITEMS.length;")
        self.assertEqual(count, 27)

    # ---------------------------------------------------------------
    # 2. normalCDF
    # ---------------------------------------------------------------
    def test_03_normalCDF_zero(self):
        """normalCDF(0) = 0.5"""
        val = self.js("return normalCDF(0);")
        self.assertAlmostEqual(val, 0.5, places=3)

    def test_04_normalCDF_positive(self):
        """normalCDF(1.96) ~ 0.975"""
        val = self.js("return normalCDF(1.96);")
        self.assertAlmostEqual(val, 0.975, places=2)

    # ---------------------------------------------------------------
    # 3. chi2cdf
    # ---------------------------------------------------------------
    def test_05_chi2cdf_zero(self):
        """chi2cdf(0, df) = 0"""
        val = self.js("return chi2cdf(0, 5);")
        self.assertAlmostEqual(val, 0.0, places=6)

    def test_06_chi2cdf_known(self):
        """chi2cdf(3.84, 1) ~ 0.95 (chi-squared critical value)"""
        val = self.js("return chi2cdf(3.84, 1);")
        self.assertAlmostEqual(val, 0.95, places=2)

    # ---------------------------------------------------------------
    # 4. logGamma
    # ---------------------------------------------------------------
    def test_07_logGamma_1(self):
        """logGamma(1) = 0 since Gamma(1) = 0! = 1"""
        val = self.js("return logGamma(1);")
        self.assertAlmostEqual(val, 0.0, places=5)

    def test_08_logGamma_5(self):
        """logGamma(5) = ln(4!) = ln(24) ~ 3.178"""
        val = self.js("return logGamma(5);")
        self.assertAlmostEqual(val, math.log(24), places=3)

    # ---------------------------------------------------------------
    # 5. isRatioMeasure
    # ---------------------------------------------------------------
    def test_09_isRatioMeasure(self):
        """RR, OR, HR are ratio measures; MD is not"""
        self.assertTrue(self.js("return isRatioMeasure('RR');"))
        self.assertTrue(self.js("return isRatioMeasure('OR');"))
        self.assertTrue(self.js("return isRatioMeasure('HR');"))
        self.assertFalse(self.js("return isRatioMeasure('MD');"))
        self.assertFalse(self.js("return isRatioMeasure('SMD');"))

    # ---------------------------------------------------------------
    # 6. Default example loads on init
    # ---------------------------------------------------------------
    def test_10_default_example_loaded(self):
        """App should load example 0 (sex example) on init with 12 studies"""
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 12, "Default example should load 12 studies")

    def test_11_default_example_has_gender_subgroups(self):
        """Default example studies should have Gender subgroups"""
        has_gender = self.js("""
            return state.studies.every(function(s){
                return s.subgroups.some(function(sg){ return sg.dim === 'Gender'; });
            });
        """)
        self.assertTrue(has_gender, "All default studies should have Gender subgroups")

    # ---------------------------------------------------------------
    # 7. DL random-effects meta-analysis
    # ---------------------------------------------------------------
    def test_12_pooled_effects_single_study(self):
        """Single-study pooling returns that study's effect"""
        result = self.js("""
            var studies = [{effect: 0.80, lower: 0.70, upper: 0.91}];
            return pooledEffects(studies, 'RR');
        """)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['effect'], 0.80, places=2)
        self.assertEqual(result['k'], 1)

    def test_13_pooled_effects_multiple_studies(self):
        """Multi-study DL pooling returns valid result"""
        result = self.js("""
            var studies = [
                {effect: 0.80, lower: 0.65, upper: 0.98},
                {effect: 0.75, lower: 0.60, upper: 0.94},
                {effect: 0.90, lower: 0.78, upper: 1.04}
            ];
            return pooledEffects(studies, 'RR');
        """)
        self.assertIsNotNone(result)
        self.assertEqual(result['k'], 3)
        # Pooled effect should be between min and max study effects
        self.assertGreaterEqual(result['effect'], 0.70)
        self.assertLessEqual(result['effect'], 0.95)
        # I2 should be between 0 and 100
        self.assertGreaterEqual(result['I2'], 0)
        self.assertLessEqual(result['I2'], 100)

    def test_14_pooled_effects_md(self):
        """Pooling mean differences (non-ratio measure)"""
        result = self.js("""
            var studies = [
                {effect: -2.5, lower: -4.0, upper: -1.0},
                {effect: -3.0, lower: -5.0, upper: -1.0},
                {effect: -1.5, lower: -3.0, upper: 0.0}
            ];
            return pooledEffects(studies, 'MD');
        """)
        self.assertIsNotNone(result)
        # Pooled MD should be negative
        self.assertLess(result['effect'], 0)
        # Lower CI should be less than upper
        self.assertLess(result['lower'], result['upper'])

    # ---------------------------------------------------------------
    # 8. Interaction test
    # ---------------------------------------------------------------
    def test_15_interaction_test(self):
        """Interaction test between subgroups returns valid statistics"""
        result = self.js("""
            var sgResults = [
                { label: 'Female', studies: [{effect:0.72,lower:0.60,upper:0.86},{effect:0.80,lower:0.65,upper:0.98}],
                  pool: pooledEffects([{effect:0.72,lower:0.60,upper:0.86},{effect:0.80,lower:0.65,upper:0.98}], 'RR') },
                { label: 'Male', studies: [{effect:0.95,lower:0.80,upper:1.13},{effect:1.05,lower:0.85,upper:1.30}],
                  pool: pooledEffects([{effect:0.95,lower:0.80,upper:1.13},{effect:1.05,lower:0.85,upper:1.30}], 'RR') }
            ];
            return interactionTest(sgResults, 'RR');
        """)
        self.assertIsNotNone(result)
        self.assertIn('Qbetween', result)
        self.assertIn('pBetween', result)
        self.assertIn('dfBetween', result)
        self.assertEqual(result['dfBetween'], 1)
        # p should be between 0 and 1
        self.assertGreaterEqual(result['pBetween'], 0)
        self.assertLessEqual(result['pBetween'], 1)
        # Effect ratio should be computed (2 subgroups)
        self.assertIsNotNone(result['effectRatio'])

    def test_16_interaction_test_single_subgroup(self):
        """Interaction test with <2 subgroups returns null"""
        result = self.js("""
            var sgResults = [
                { label: 'Female', studies: [{effect:0.80,lower:0.70,upper:0.91}],
                  pool: pooledEffects([{effect:0.80,lower:0.70,upper:0.91}], 'RR') }
            ];
            return interactionTest(sgResults, 'RR');
        """)
        self.assertIsNone(result)

    # ---------------------------------------------------------------
    # 9. Study management
    # ---------------------------------------------------------------
    def test_17_clear_all_data(self):
        """clearAllData empties studies (with confirmation bypassed)"""
        self.js("""
            window._origConfirm = window.confirm;
            window.confirm = function() { return true; };
            clearAllData();
            window.confirm = window._origConfirm;
        """)
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 0)

    def test_18_add_study_programmatically(self):
        """Adding a study via UI inputs works"""
        self.js("""
            // First clear
            window._origConfirm = window.confirm;
            window.confirm = function() { return true; };
            clearAllData();
            window.confirm = window._origConfirm;

            document.getElementById('inp-study-name').value = 'TestStudy2020';
            document.getElementById('inp-study-year').value = '2020';
            document.getElementById('inp-effect-type').value = 'RR';
            document.getElementById('inp-effect').value = '0.85';
            document.getElementById('inp-lower').value = '0.70';
            document.getElementById('inp-upper').value = '1.03';
            document.getElementById('inp-n').value = '500';
            addStudy();
        """)
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 1)
        name = self.js("return state.studies[0].name;")
        self.assertEqual(name, 'TestStudy2020')

    def test_19_delete_study(self):
        """Deleting a study removes it from state"""
        study_id = self.js("return state.studies[0].id;")
        self.js(f"deleteStudy({study_id});")
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 0)

    # ---------------------------------------------------------------
    # 10. Subgroup management
    # ---------------------------------------------------------------
    def test_20_add_pending_subgroup(self):
        """Adding a pending subgroup stages it before adding study"""
        self.js("""
            pendingSubgroups = [];
            document.getElementById('inp-sg-dim').value = 'Gender';
            document.getElementById('inp-sg-label').value = 'Female';
            document.getElementById('inp-sg-effect').value = '0.75';
            document.getElementById('inp-sg-lower').value = '0.60';
            document.getElementById('inp-sg-upper').value = '0.93';
            document.getElementById('inp-sg-n').value = '250';
            addPendingSubgroup();
        """)
        count = self.js("return pendingSubgroups.length;")
        self.assertEqual(count, 1)
        self.assertEqual(self.js("return pendingSubgroups[0].dim;"), 'Gender')

    def test_21_study_with_subgroups(self):
        """Study added with pending subgroups includes them"""
        self.js("""
            // Keep existing pending subgroups and add study
            document.getElementById('inp-study-name').value = 'SubgroupStudy';
            document.getElementById('inp-study-year').value = '2021';
            document.getElementById('inp-effect-type').value = 'RR';
            document.getElementById('inp-effect').value = '0.80';
            document.getElementById('inp-lower').value = '0.68';
            document.getElementById('inp-upper').value = '0.94';
            document.getElementById('inp-n').value = '600';
            addStudy();
        """)
        last_study = self.js("return state.studies[state.studies.length - 1];")
        self.assertEqual(last_study['name'], 'SubgroupStudy')
        self.assertEqual(len(last_study['subgroups']), 1)
        self.assertEqual(last_study['subgroups'][0]['dim'], 'Gender')

    # ---------------------------------------------------------------
    # 11. CSV import
    # ---------------------------------------------------------------
    def test_22_csv_import(self):
        """CSV import parses and adds studies"""
        self.js("""
            window._origConfirm = window.confirm;
            window.confirm = function() { return true; };
            clearAllData();
            window.confirm = window._origConfirm;
        """)
        csv_data = "StudyA,2019,RR,0.85,0.72,1.00,400,Gender,Female,0.78,0.62,0.98,200\\nStudyA,2019,RR,0.85,0.72,1.00,400,Gender,Male,0.92,0.75,1.12,200\\nStudyB,2020,RR,0.90,0.80,1.02,600,,,,,,,"
        self.js(f"""
            document.getElementById('csv-pane').style.display = '';
            document.getElementById('csv-paste').value = '{csv_data}';
            importCsv();
        """)
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 2, "Should import 2 unique studies")
        studyA_sgs = self.js("""
            var s = state.studies.find(function(s){ return s.name === 'StudyA'; });
            return s ? s.subgroups.length : -1;
        """)
        self.assertEqual(studyA_sgs, 2, "StudyA should have 2 subgroups")

    # ---------------------------------------------------------------
    # 12. Tab switching
    # ---------------------------------------------------------------
    def test_23_tab_switching_data(self):
        """Switching to data tab shows studies panel"""
        self.js("switchTab('data');")
        time.sleep(0.3)
        active = self.js("return document.getElementById('panel-data').classList.contains('active');")
        self.assertTrue(active)

    def test_24_tab_switching_analysis(self):
        """Switching to analysis tab renders analysis content"""
        self.js("switchTab('analysis');")
        time.sleep(0.3)
        active = self.js("return document.getElementById('panel-analysis').classList.contains('active');")
        self.assertTrue(active)

    def test_25_tab_switching_prisma(self):
        """Switching to prisma tab renders checklist"""
        self.js("switchTab('prisma');")
        time.sleep(0.5)
        body = self.js("return document.getElementById('prisma-checklist-body').innerHTML;")
        self.assertGreater(len(body), 0, "PRISMA checklist body should have content")

    # ---------------------------------------------------------------
    # 13. Load examples
    # ---------------------------------------------------------------
    def test_26_load_example_sex(self):
        """Load sex/gender example (12 studies with Gender dimension)"""
        self.js("loadExample(0);")
        time.sleep(0.5)
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 12)
        # loadExample resets selectedDim to null after loading; verify Gender subgroups exist
        has_gender = self.js("return state.studies[0].subgroups.some(function(sg){return sg.dim==='Gender';});")
        self.assertTrue(has_gender, "Studies should have Gender subgroups")

    def test_27_load_example_ses(self):
        """Load SES example (8 studies)"""
        self.js("loadExample(1);")
        time.sleep(0.5)
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 8)
        # Verify SES subgroups exist in some studies (not all have SES data)
        has_ses = self.js("return state.studies.some(function(s){return s.subgroups.some(function(sg){return sg.dim==='SES';});});")
        self.assertTrue(has_ses, "Some studies should have SES subgroups")

    def test_28_load_example_lic(self):
        """Load LIC/HIC example (15 studies with Place dimension)"""
        self.js("loadExample(2);")
        time.sleep(0.5)
        count = self.js("return state.studies.length;")
        self.assertEqual(count, 15)
        # Verify Place subgroups exist in some studies
        has_place = self.js("return state.studies.some(function(s){return s.subgroups.some(function(sg){return sg.dim==='Place';});});")
        self.assertTrue(has_place, "Some studies should have Place subgroups")

    # ---------------------------------------------------------------
    # 14. PRISMA-E checklist
    # ---------------------------------------------------------------
    def test_29_prisma_toggle_item(self):
        """Toggling a PRISMA item updates state"""
        self.js("switchTab('prisma');")
        time.sleep(0.5)
        self.js("""
            state.prismaChecked = {};
            document.getElementById('chk-T1').checked = true;
            togglePrismaItem('T1');
        """)
        checked = self.js("return state.prismaChecked['T1'];")
        self.assertTrue(checked)

    def test_30_prisma_auto_fill(self):
        """Auto-fill PRISMA based on data populates items"""
        self.js("loadExample(0);")
        time.sleep(0.3)
        self.js("state.prismaChecked = {};")
        self.js("autoFillPrisma();")
        time.sleep(0.3)
        filled = self.js("return Object.values(state.prismaChecked).filter(Boolean).length;")
        self.assertGreater(filled, 0, "Auto-fill should check some items")
        # I2 should be checked (has PROGRESS dims)
        self.assertTrue(self.js("return state.prismaChecked['I2'] === true;"))

    def test_31_prisma_progress_bar(self):
        """PRISMA progress bar reflects checked items"""
        self.js("switchTab('prisma');")
        time.sleep(0.5)
        text = self.js("return document.getElementById('prisma-progress-text').textContent;")
        self.assertIn('/', text, "Progress text should show x / 27 items")

    # ---------------------------------------------------------------
    # 15. PROGRESS-Plus coverage
    # ---------------------------------------------------------------
    def test_32_coverage_rendering(self):
        """Coverage grid renders dimension cards"""
        self.js("loadExample(0);")
        time.sleep(0.3)
        self.js("renderCoverage();")
        html = self.js("return document.getElementById('progress-coverage-grid').innerHTML;")
        self.assertIn('Gender', html)

    # ---------------------------------------------------------------
    # 16. Analysis: DL meta pooling on default example
    # ---------------------------------------------------------------
    def test_33_analysis_overall_pooling(self):
        """Overall pooled RR from sex example should be ~0.90-0.95"""
        self.js("loadExample(0);")
        time.sleep(0.3)
        result = self.js("""
            return pooledEffects(state.studies, 'RR');
        """)
        self.assertIsNotNone(result)
        # 12 large trials, pooled RR should be around 0.90-0.95
        self.assertGreater(result['effect'], 0.80)
        self.assertLess(result['effect'], 1.0)
        self.assertEqual(result['k'], 12)

    # ---------------------------------------------------------------
    # 17. Interaction test on full example
    # ---------------------------------------------------------------
    def test_34_interaction_test_sex_example(self):
        """Gender interaction test from sex example produces valid Q_between"""
        result = self.js("""
            var femaleStudies = state.studies.map(function(s){
                var sg = s.subgroups.find(function(g){return g.label==='Female';});
                return sg ? {effect:sg.effect, lower:sg.lower, upper:sg.upper, n:sg.n} : null;
            }).filter(Boolean);
            var maleStudies = state.studies.map(function(s){
                var sg = s.subgroups.find(function(g){return g.label==='Male';});
                return sg ? {effect:sg.effect, lower:sg.lower, upper:sg.upper, n:sg.n} : null;
            }).filter(Boolean);

            var sgResults = [
                {label:'Female', studies:femaleStudies, pool: pooledEffects(femaleStudies, 'RR')},
                {label:'Male', studies:maleStudies, pool: pooledEffects(maleStudies, 'RR')}
            ];
            return interactionTest(sgResults, 'RR');
        """)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result['Qbetween'], 0)
        self.assertEqual(result['dfBetween'], 1)
        self.assertIsNotNone(result['effectRatio'])

    # ---------------------------------------------------------------
    # 18. Dark mode toggle
    # ---------------------------------------------------------------
    def test_35_dark_mode_toggle(self):
        """Dark mode toggle adds/removes class on body"""
        self.js("toggleDark();")
        has_dark = self.js("return document.body.classList.contains('dark');")
        self.assertTrue(has_dark)
        self.js("toggleDark();")
        has_dark = self.js("return document.body.classList.contains('dark');")
        self.assertFalse(has_dark)

    # ---------------------------------------------------------------
    # 19. localStorage
    # ---------------------------------------------------------------
    def test_36_localstorage_key(self):
        """App uses correct localStorage key"""
        self.js("saveState();")
        val = self.js("return localStorage.getItem('equityma_state_v1');")
        self.assertIsNotNone(val)
        self.assertIn('studies', val)

    # ---------------------------------------------------------------
    # 20. escHtml
    # ---------------------------------------------------------------
    def test_37_escHtml(self):
        """escHtml escapes dangerous characters"""
        result = self.js("return escHtml('<script>alert(1)</script>');")
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;', result)

    def test_38_escHtml_null(self):
        """escHtml handles null"""
        result = self.js("return escHtml(null);")
        self.assertEqual(result, '')

    # ---------------------------------------------------------------
    # 21. fmtEffect
    # ---------------------------------------------------------------
    def test_39_fmtEffect(self):
        """fmtEffect formats effect with CI"""
        result = self.js("return fmtEffect(0.85, 0.72, 1.00);")
        self.assertIn('0.85', result)
        self.assertIn('0.72', result)

    def test_40_fmtEffect_null(self):
        """fmtEffect handles null effect"""
        result = self.js("return fmtEffect(null, 0, 0);")
        self.assertIn('\u2014', result)  # em-dash

    # ---------------------------------------------------------------
    # 22. Studies table rendering
    # ---------------------------------------------------------------
    def test_41_studies_table_rendering(self):
        """Studies table shows rows for loaded data"""
        self.js("loadExample(0);")
        time.sleep(0.3)
        rows = self.js("return document.getElementById('studies-tbody').querySelectorAll('tr').length;")
        self.assertEqual(rows, 12)

    # ---------------------------------------------------------------
    # 23. Edge case: empty studies pooling
    # ---------------------------------------------------------------
    def test_42_pooled_effects_empty(self):
        """pooledEffects returns null for empty studies array"""
        result = self.js("return pooledEffects([], 'RR');")
        self.assertIsNone(result)

    # ---------------------------------------------------------------
    # 24. getAvailableDims
    # ---------------------------------------------------------------
    def test_43_get_available_dims(self):
        """getAvailableDims returns dims present in data"""
        self.js("loadExample(0);")
        dims = self.js("return getAvailableDims();")
        self.assertIn('Gender', dims)

    # ---------------------------------------------------------------
    # 25. Weights sum to 100% in DL
    # ---------------------------------------------------------------
    def test_44_dl_weights_sum(self):
        """DL weights should sum to approximately 100"""
        result = self.js("""
            var studies = [
                {effect: 0.80, lower: 0.65, upper: 0.98},
                {effect: 0.90, lower: 0.78, upper: 1.04},
                {effect: 0.75, lower: 0.60, upper: 0.94}
            ];
            var r = pooledEffects(studies, 'RR');
            return r.weights.reduce(function(a,b){return a+b;}, 0);
        """)
        self.assertAlmostEqual(result, 100.0, places=1)

    # ---------------------------------------------------------------
    # 26. gammaInc accuracy for small x
    # ---------------------------------------------------------------
    def test_45_gammaInc_small_x(self):
        """gammaInc(1, 0.5) should be approx 1 - exp(-0.5) = 0.3935"""
        val = self.js("return gammaInc(1, 0.5);")
        expected = 1 - math.exp(-0.5)
        self.assertAlmostEqual(val, expected, places=3)

    # ---------------------------------------------------------------
    # 27. Study count display
    # ---------------------------------------------------------------
    def test_46_study_count_display(self):
        """Study count span updates with number of studies"""
        self.js("loadExample(0);")
        time.sleep(0.3)
        text = self.js("return document.getElementById('study-count').textContent;")
        self.assertEqual(text, '12')

    # ---------------------------------------------------------------
    # 28. Analysis renders with data
    # ---------------------------------------------------------------
    def test_47_analysis_renders_canvases(self):
        """Analysis tab creates canvas elements for plots"""
        self.js("loadExample(0);")
        time.sleep(0.3)
        self.js("switchTab('analysis');")
        time.sleep(0.5)
        overall_canvas = self.js("return document.getElementById('canvas-overall') !== null;")
        stratified_canvas = self.js("return document.getElementById('canvas-stratified') !== null;")
        self.assertTrue(overall_canvas, "Overall forest canvas should exist")
        self.assertTrue(stratified_canvas, "Stratified forest canvas should exist")

    # ---------------------------------------------------------------
    # 29. DIM_LABELS matches DIMS
    # ---------------------------------------------------------------
    def test_48_dim_labels_complete(self):
        """Each DIM has a corresponding DIM_LABELS entry"""
        result = self.js("""
            return DIMS.every(function(d){ return DIM_LABELS[d] !== undefined; });
        """)
        self.assertTrue(result)

    # ---------------------------------------------------------------
    # 30. Export CSV generation
    # ---------------------------------------------------------------
    def test_49_export_html_report_exists(self):
        """exportHtmlReport function exists and is callable"""
        exists = self.js("return typeof exportHtmlReport === 'function';")
        self.assertTrue(exists)

    def test_50_export_csv_function_exists(self):
        """exportCsvData function exists and is callable"""
        exists = self.js("return typeof exportCsvData === 'function';")
        self.assertTrue(exists)


if __name__ == '__main__':
    unittest.main(verbosity=2)
