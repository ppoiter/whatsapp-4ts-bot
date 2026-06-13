/**
 * World Cup 2026 Forms Generator and Management Script
 * 
 * This Google Apps Script creates all 4 forms for the WC 2026 tipping competition
 * and manages the master spreadsheet with triggers for form submissions.
 * 
 * SETUP SEQUENCE:
 * 1. Run createAllForms() - generates all 4 Google Forms
 * 2. Link each form to a response spreadsheet (Forms UI → Responses → Link to Sheets)
 * 3. Run createMasterSheet() - creates master spreadsheet, prints its ID
 * 4. Paste the master spreadsheet ID into MASTER_SHEET_ID below
 * 5. Run installTriggers() - installs onFormSubmit triggers for all 4 forms
 */

// CONFIGURATION - UPDATE THIS AFTER CREATING MASTER SHEET
const MASTER_SHEET_ID = ''; // Paste master spreadsheet ID here after running createMasterSheet()

// FIFA Rankings as of April 1, 2026
const FIFA_RANK = {
  "France": 1, "Spain": 2, "Argentina": 3, "England": 4, "Portugal": 5,
  "Brazil": 6, "Netherlands": 7, "Morocco": 8, "Belgium": 9, "Germany": 10,
  "Croatia": 11, "Colombia": 13, "Senegal": 14, "Mexico": 15,
  "USA": 16, "Uruguay": 17, "Japan": 18, "Switzerland": 19,
  "Iran": 21, "Turkey": 22, "Ecuador": 23, "Austria": 24,
  "South Korea": 25, "Australia": 27, "Algeria": 28, "Egypt": 29,
  "Canada": 30, "Norway": 31, "Panama": 33, "Ivory Coast": 34,
  "Sweden": 38, "Paraguay": 40, "Czechia": 41, "Scotland": 43,
  "Tunisia": 44, "DR Congo": 46, "Uzbekistan": 50, "Qatar": 55,
  "Iraq": 57, "South Africa": 60, "Saudi Arabia": 61, "Jordan": 63,
  "Bosnia & Herzegovina": 65, "Cape Verde": 69, "Ghana": 74,
  "Curacao": 82, "Haiti": 83, "New Zealand": 85
};

// Get all teams sorted by rank
function getAllTeams() {
  return Object.keys(FIFA_RANK).sort((a, b) => FIFA_RANK[a] - FIFA_RANK[b]);
}

// Get teams with ranking suffix for display
function getTeamsWithRank() {
  return getAllTeams().map(team => `${team} (#${FIFA_RANK[team]})`);
}

/**
 * STEP 1: Create all 4 forms
 */
function createAllForms() {
  console.log('Creating all 4 World Cup 2026 forms...');
  
  createForm1_PreTournament();
  createForm2_Matchday1();
  createForm3_Matchday2();
  createForm4_Matchday3();
  
  console.log('All forms created successfully!');
  console.log('Next steps:');
  console.log('1. Link each form to a response spreadsheet');
  console.log('2. Run createMasterSheet()');
}

/**
 * Form 1: Pre-Tournament Picks
 */
function createForm1_PreTournament() {
  const form = FormApp.create('WC 2026 - Pre-Tournament Picks');
  form.setDescription('Submit your pre-tournament predictions for World Cup 2026. Deadline: before kick-off on 11 June.');
  
  // Your name
  form.addTextItem()
    .setTitle('Your name')
    .setRequired(true);
  
  // Tournament Winner
  const teams = getTeamsWithRank();
  form.addListItem()
    .setTitle('Tournament Winner')
    .setChoiceValues(teams)
    .setRequired(true);
  
  // Golden Boot Winner
  form.addListItem()
    .setTitle('Golden Boot Winner')
    .setChoiceValues(teams)
    .setRequired(false);
  
  // Group Winners
  const groups = [
    { letter: 'A', teams: ['Mexico (#15)', 'South Korea (#25)', 'Czechia (#41)', 'South Africa (#60)'] },
    { letter: 'B', teams: ['Canada (#30)', 'Qatar (#55)', 'Switzerland (#19)', 'Bosnia & Herzegovina (#65)'] },
    { letter: 'C', teams: ['Brazil (#6)', 'Morocco (#8)', 'Haiti (#83)', 'Scotland (#43)'] },
    { letter: 'D', teams: ['USA (#16)', 'Paraguay (#40)', 'Turkey (#22)', 'Australia (#27)'] },
    { letter: 'E', teams: ['Germany (#10)', 'Ivory Coast (#34)', 'Ecuador (#23)', 'Curacao (#82)'] },
    { letter: 'F', teams: ['Netherlands (#7)', 'Japan (#18)', 'Sweden (#38)', 'Tunisia (#44)'] },
    { letter: 'G', teams: ['Belgium (#9)', 'Egypt (#29)', 'Iran (#21)', 'New Zealand (#85)'] },
    { letter: 'H', teams: ['Spain (#2)', 'Uruguay (#17)', 'Saudi Arabia (#61)', 'Cape Verde (#69)'] },
    { letter: 'I', teams: ['France (#1)', 'Senegal (#14)', 'Iraq (#57)', 'Norway (#31)'] },
    { letter: 'J', teams: ['Argentina (#3)', 'Algeria (#28)', 'Austria (#24)', 'Jordan (#63)'] },
    { letter: 'K', teams: ['Portugal (#5)', 'DR Congo (#46)', 'Uzbekistan (#50)', 'Colombia (#13)'] },
    { letter: 'L', teams: ['England (#4)', 'Croatia (#11)', 'Ghana (#74)', 'Panama (#33)'] }
  ];
  
  for (const group of groups) {
    form.addMultipleChoiceItem()
      .setTitle(`Group ${group.letter} Winner`)
      .setChoiceValues(group.teams)
      .setRequired(true);
  }
  
  // Bonus: Red card team
  form.addListItem()
    .setTitle('Bonus: Pick a team to receive a red card')
    .setChoiceValues(teams)
    .setRequired(false);
  
  console.log(`Form 1 created: ${form.getPublishedUrl()}`);
  return form.getId();
}

/**
 * Form 2: Matchday 1
 */
function createForm2_Matchday1() {
  const form = FormApp.create('WC 2026 - Matchday 1');
  form.setDescription('Submit your predictions for Matchday 1. Deadline: before kick-off on 11 June.');
  
  // Your name
  form.addTextItem()
    .setTitle('Your name')
    .setRequired(true);
  
  // Matchday 1 fixtures
  const fixtures = [
    { home: 'Mexico (#15)', away: 'South Africa (#60)', group: 'A' },
    { home: 'South Korea (#25)', away: 'Czechia (#41)', group: 'A' },
    { home: 'Canada (#30)', away: 'Bosnia & Herzegovina (#65)', group: 'B' },
    { home: 'Qatar (#55)', away: 'Switzerland (#19)', group: 'B' },
    { home: 'Brazil (#6)', away: 'Morocco (#8)', group: 'C' },
    { home: 'Haiti (#83)', away: 'Scotland (#43)', group: 'C' },
    { home: 'USA (#16)', away: 'Paraguay (#40)', group: 'D' },
    { home: 'Australia (#27)', away: 'Turkey (#22)', group: 'D' },
    { home: 'Germany (#10)', away: 'Curacao (#82)', group: 'E' },
    { home: 'Ivory Coast (#34)', away: 'Ecuador (#23)', group: 'E' },
    { home: 'Netherlands (#7)', away: 'Japan (#18)', group: 'F' },
    { home: 'Sweden (#38)', away: 'Tunisia (#44)', group: 'F' },
    { home: 'Belgium (#9)', away: 'Egypt (#29)', group: 'G' },
    { home: 'Iran (#21)', away: 'New Zealand (#85)', group: 'G' },
    { home: 'Spain (#2)', away: 'Cape Verde (#69)', group: 'H' },
    { home: 'Saudi Arabia (#61)', away: 'Uruguay (#17)', group: 'H' },
    { home: 'France (#1)', away: 'Senegal (#14)', group: 'I' },
    { home: 'Iraq (#57)', away: 'Norway (#31)', group: 'I' },
    { home: 'Argentina (#3)', away: 'Algeria (#28)', group: 'J' },
    { home: 'Austria (#24)', away: 'Jordan (#63)', group: 'J' },
    { home: 'Portugal (#5)', away: 'DR Congo (#46)', group: 'K' },
    { home: 'Uzbekistan (#50)', away: 'Colombia (#13)', group: 'K' },
    { home: 'England (#4)', away: 'Croatia (#11)', group: 'L' },
    { home: 'Ghana (#74)', away: 'Panama (#33)', group: 'L' }
  ];
  
  for (const fixture of fixtures) {
    const homeTeam = fixture.home.replace(/ \(#\d+\)/, '');
    const awayTeam = fixture.away.replace(/ \(#\d+\)/, '');
    
    form.addMultipleChoiceItem()
      .setTitle(`${fixture.home} vs ${fixture.away}`)
      .setChoiceValues(['Home', 'Draw', 'Away'])
      .setRequired(true);
  }
  
  // Bonus: Red card team in Matchday 1
  const teams = getTeamsWithRank();
  form.addListItem()
    .setTitle('Bonus: Pick a team to receive a red card in Matchday 1')
    .setChoiceValues(teams)
    .setRequired(false);
  
  console.log(`Form 2 created: ${form.getPublishedUrl()}`);
  return form.getId();
}

/**
 * Form 3: Matchday 2
 */
function createForm3_Matchday2() {
  const form = FormApp.create('WC 2026 - Matchday 2');
  form.setDescription('Submit your predictions for Matchday 2. Deadline: before first kick-off on 18 June.');
  
  // Your name
  form.addTextItem()
    .setTitle('Your name')
    .setRequired(true);
  
  // Matchday 2 fixtures
  const fixtures = [
    { home: 'Czechia (#41)', away: 'South Africa (#60)', group: 'A' },
    { home: 'Mexico (#15)', away: 'South Korea (#25)', group: 'A' },
    { home: 'Switzerland (#19)', away: 'Bosnia & Herzegovina (#65)', group: 'B' },
    { home: 'Canada (#30)', away: 'Qatar (#55)', group: 'B' },
    { home: 'Scotland (#43)', away: 'Morocco (#8)', group: 'C' },
    { home: 'Brazil (#6)', away: 'Haiti (#83)', group: 'C' },
    { home: 'USA (#16)', away: 'Australia (#27)', group: 'D' },
    { home: 'Turkey (#22)', away: 'Paraguay (#40)', group: 'D' },
    { home: 'Germany (#10)', away: 'Ivory Coast (#34)', group: 'E' },
    { home: 'Ecuador (#23)', away: 'Curacao (#82)', group: 'E' },
    { home: 'Netherlands (#7)', away: 'Sweden (#38)', group: 'F' },
    { home: 'Tunisia (#44)', away: 'Japan (#18)', group: 'F' },
    { home: 'Belgium (#9)', away: 'Iran (#21)', group: 'G' },
    { home: 'New Zealand (#85)', away: 'Egypt (#29)', group: 'G' },
    { home: 'Spain (#2)', away: 'Saudi Arabia (#61)', group: 'H' },
    { home: 'Uruguay (#17)', away: 'Cape Verde (#69)', group: 'H' },
    { home: 'France (#1)', away: 'Iraq (#57)', group: 'I' },
    { home: 'Norway (#31)', away: 'Senegal (#14)', group: 'I' },
    { home: 'Argentina (#3)', away: 'Austria (#24)', group: 'J' },
    { home: 'Jordan (#63)', away: 'Algeria (#28)', group: 'J' },
    { home: 'Portugal (#5)', away: 'Uzbekistan (#50)', group: 'K' },
    { home: 'Colombia (#13)', away: 'DR Congo (#46)', group: 'K' },
    { home: 'England (#4)', away: 'Ghana (#74)', group: 'L' },
    { home: 'Panama (#33)', away: 'Croatia (#11)', group: 'L' }
  ];
  
  for (const fixture of fixtures) {
    form.addMultipleChoiceItem()
      .setTitle(`${fixture.home} vs ${fixture.away}`)
      .setChoiceValues(['Home', 'Draw', 'Away'])
      .setRequired(true);
  }
  
  // Bonus: Fewest corners match
  const matchOptions = fixtures.map(f => {
    const home = f.home.replace(/ \(#\d+\)/, '');
    const away = f.away.replace(/ \(#\d+\)/, '');
    return `${home} vs ${away}`;
  });
  
  form.addMultipleChoiceItem()
    .setTitle('Bonus: Pick the match with the fewest corners in Matchday 2')
    .setChoiceValues(matchOptions)
    .setRequired(false);
  
  console.log(`Form 3 created: ${form.getPublishedUrl()}`);
  return form.getId();
}

/**
 * Form 4: Matchday 3
 */
function createForm4_Matchday3() {
  const form = FormApp.create('WC 2026 - Matchday 3');
  form.setDescription('Submit your predictions for Matchday 3. Deadline: before first kick-off on 24 June.');
  
  // Your name
  form.addTextItem()
    .setTitle('Your name')
    .setRequired(true);
  
  // Matchday 3 fixtures
  const fixtures = [
    { home: 'Czechia (#41)', away: 'Mexico (#15)', group: 'A', date: 'Jun 24' },
    { home: 'South Africa (#60)', away: 'South Korea (#25)', group: 'A', date: 'Jun 24' },
    { home: 'Switzerland (#19)', away: 'Canada (#30)', group: 'B', date: 'Jun 24' },
    { home: 'Bosnia & Herzegovina (#65)', away: 'Qatar (#55)', group: 'B', date: 'Jun 24' },
    { home: 'Scotland (#43)', away: 'Brazil (#6)', group: 'C', date: 'Jun 24' },
    { home: 'Morocco (#8)', away: 'Haiti (#83)', group: 'C', date: 'Jun 24' },
    { home: 'Turkey (#22)', away: 'USA (#16)', group: 'D', date: 'Jun 25' },
    { home: 'Paraguay (#40)', away: 'Australia (#27)', group: 'D', date: 'Jun 25' },
    { home: 'Ecuador (#23)', away: 'Germany (#10)', group: 'E', date: 'Jun 25' },
    { home: 'Curacao (#82)', away: 'Ivory Coast (#34)', group: 'E', date: 'Jun 25' },
    { home: 'Japan (#18)', away: 'Sweden (#38)', group: 'F', date: 'Jun 25' },
    { home: 'Tunisia (#44)', away: 'Netherlands (#7)', group: 'F', date: 'Jun 25' },
    { home: 'Egypt (#29)', away: 'Iran (#21)', group: 'G', date: 'Jun 26' },
    { home: 'New Zealand (#85)', away: 'Belgium (#9)', group: 'G', date: 'Jun 26' },
    { home: 'Cape Verde (#69)', away: 'Saudi Arabia (#61)', group: 'H', date: 'Jun 26' },
    { home: 'Uruguay (#17)', away: 'Spain (#2)', group: 'H', date: 'Jun 26' },
    { home: 'Norway (#31)', away: 'France (#1)', group: 'I', date: 'Jun 26' },
    { home: 'Senegal (#14)', away: 'Iraq (#57)', group: 'I', date: 'Jun 26' },
    { home: 'Algeria (#28)', away: 'Austria (#24)', group: 'J', date: 'Jun 27' },
    { home: 'Jordan (#63)', away: 'Argentina (#3)', group: 'J', date: 'Jun 27' },
    { home: 'Colombia (#13)', away: 'Portugal (#5)', group: 'K', date: 'Jun 27' },
    { home: 'DR Congo (#46)', away: 'Uzbekistan (#50)', group: 'K', date: 'Jun 27' },
    { home: 'Panama (#33)', away: 'England (#4)', group: 'L', date: 'Jun 27' },
    { home: 'Croatia (#11)', away: 'Ghana (#74)', group: 'L', date: 'Jun 27' }
  ];
  
  for (const fixture of fixtures) {
    form.addMultipleChoiceItem()
      .setTitle(`${fixture.home} vs ${fixture.away}`)
      .setChoiceValues(['Home', 'Draw', 'Away'])
      .setRequired(true);
  }
  
  // Bonus: Earliest card match
  const matchOptions = fixtures.map(f => {
    const home = f.home.replace(/ \(#\d+\)/, '');
    const away = f.away.replace(/ \(#\d+\)/, '');
    return `${home} vs ${away}`;
  });
  
  form.addMultipleChoiceItem()
    .setTitle('Bonus: Pick the game with the earliest card in Matchday 3')
    .setChoiceValues(matchOptions)
    .setRequired(false);
  
  console.log(`Form 4 created: ${form.getPublishedUrl()}`);
  return form.getId();
}

/**
 * STEP 3: Create master spreadsheet with all tabs
 */
function createMasterSheet() {
  console.log('Creating master spreadsheet...');
  
  const ss = SpreadsheetApp.create('WC 2026 - Master Sheet');
  const id = ss.getId();
  
  // Remove default sheet
  const defaultSheet = ss.getSheets()[0];
  
  // Create form response tabs
  createFormResponseTab(ss, 'form1_picks', getForm1Headers());
  createFormResponseTab(ss, 'form2_picks', getForm2Headers());
  createFormResponseTab(ss, 'form3_picks', getForm3Headers());
  createFormResponseTab(ss, 'form4_picks', getForm4Headers());
  
  // Create results tab
  const resultsSheet = ss.insertSheet('results');
  resultsSheet.getRange(1, 1, 1, 6).setValues([[
    'match_key', 'home_score', 'away_score', 'stage', 'matchday', 'logged_at'
  ]]);
  
  // Create bonus tab
  const bonusSheet = ss.insertSheet('bonus');
  bonusSheet.getRange(1, 1, 1, 4).setValues([[
    'form', 'player', 'points', 'awarded_at'
  ]]);
  
  // Remove default sheet
  ss.deleteSheet(defaultSheet);
  
  console.log(`Master spreadsheet created with ID: ${id}`);
  console.log(`URL: ${ss.getUrl()}`);
  console.log('Next steps:');
  console.log('1. Copy the spreadsheet ID above');
  console.log('2. Paste it into MASTER_SHEET_ID at the top of this script');
  console.log('3. Run installTriggers()');
  
  return id;
}

function createFormResponseTab(spreadsheet, tabName, headers) {
  const sheet = spreadsheet.insertSheet(tabName);
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  return sheet;
}

function getForm1Headers() {
  return [
    'Timestamp', 'Your name', 'Tournament Winner', 'Golden Boot Winner',
    'Group A Winner', 'Group B Winner', 'Group C Winner', 'Group D Winner',
    'Group E Winner', 'Group F Winner', 'Group G Winner', 'Group H Winner',
    'Group I Winner', 'Group J Winner', 'Group K Winner', 'Group L Winner',
    'Bonus: Pick a team to receive a red card'
  ];
}

function getForm2Headers() {
  const headers = ['Timestamp', 'Your name'];
  
  // Add all MD1 fixture headers
  const fixtures = [
    'Mexico (#15) vs South Africa (#60)', 'South Korea (#25) vs Czechia (#41)',
    'Canada (#30) vs Bosnia & Herzegovina (#65)', 'Qatar (#55) vs Switzerland (#19)',
    'Brazil (#6) vs Morocco (#8)', 'Haiti (#83) vs Scotland (#43)',
    'USA (#16) vs Paraguay (#40)', 'Australia (#27) vs Turkey (#22)',
    'Germany (#10) vs Curacao (#82)', 'Ivory Coast (#34) vs Ecuador (#23)',
    'Netherlands (#7) vs Japan (#18)', 'Sweden (#38) vs Tunisia (#44)',
    'Belgium (#9) vs Egypt (#29)', 'Iran (#21) vs New Zealand (#85)',
    'Spain (#2) vs Cape Verde (#69)', 'Saudi Arabia (#61) vs Uruguay (#17)',
    'France (#1) vs Senegal (#14)', 'Iraq (#57) vs Norway (#31)',
    'Argentina (#3) vs Algeria (#28)', 'Austria (#24) vs Jordan (#63)',
    'Portugal (#5) vs DR Congo (#46)', 'Uzbekistan (#50) vs Colombia (#13)',
    'England (#4) vs Croatia (#11)', 'Ghana (#74) vs Panama (#33)'
  ];
  
  headers.push(...fixtures);
  headers.push('Bonus: Pick a team to receive a red card in Matchday 1');
  
  return headers;
}

function getForm3Headers() {
  const headers = ['Timestamp', 'Your name'];
  
  // Add all MD2 fixture headers
  const fixtures = [
    'Czechia (#41) vs South Africa (#60)', 'Mexico (#15) vs South Korea (#25)',
    'Switzerland (#19) vs Bosnia & Herzegovina (#65)', 'Canada (#30) vs Qatar (#55)',
    'Scotland (#43) vs Morocco (#8)', 'Brazil (#6) vs Haiti (#83)',
    'USA (#16) vs Australia (#27)', 'Turkey (#22) vs Paraguay (#40)',
    'Germany (#10) vs Ivory Coast (#34)', 'Ecuador (#23) vs Curacao (#82)',
    'Netherlands (#7) vs Sweden (#38)', 'Tunisia (#44) vs Japan (#18)',
    'Belgium (#9) vs Iran (#21)', 'New Zealand (#85) vs Egypt (#29)',
    'Spain (#2) vs Saudi Arabia (#61)', 'Uruguay (#17) vs Cape Verde (#69)',
    'France (#1) vs Iraq (#57)', 'Norway (#31) vs Senegal (#14)',
    'Argentina (#3) vs Austria (#24)', 'Jordan (#63) vs Algeria (#28)',
    'Portugal (#5) vs Uzbekistan (#50)', 'Colombia (#13) vs DR Congo (#46)',
    'England (#4) vs Ghana (#74)', 'Panama (#33) vs Croatia (#11)'
  ];
  
  headers.push(...fixtures);
  headers.push('Bonus: Pick the match with the fewest corners in Matchday 2');
  
  return headers;
}

function getForm4Headers() {
  const headers = ['Timestamp', 'Your name'];
  
  // Add all MD3 fixture headers
  const fixtures = [
    'Czechia (#41) vs Mexico (#15)', 'South Africa (#60) vs South Korea (#25)',
    'Switzerland (#19) vs Canada (#30)', 'Bosnia & Herzegovina (#65) vs Qatar (#55)',
    'Scotland (#43) vs Brazil (#6)', 'Morocco (#8) vs Haiti (#83)',
    'Turkey (#22) vs USA (#16)', 'Paraguay (#40) vs Australia (#27)',
    'Ecuador (#23) vs Germany (#10)', 'Curacao (#82) vs Ivory Coast (#34)',
    'Japan (#18) vs Sweden (#38)', 'Tunisia (#44) vs Netherlands (#7)',
    'Egypt (#29) vs Iran (#21)', 'New Zealand (#85) vs Belgium (#9)',
    'Cape Verde (#69) vs Saudi Arabia (#61)', 'Uruguay (#17) vs Spain (#2)',
    'Norway (#31) vs France (#1)', 'Senegal (#14) vs Iraq (#57)',
    'Algeria (#28) vs Austria (#24)', 'Jordan (#63) vs Argentina (#3)',
    'Colombia (#13) vs Portugal (#5)', 'DR Congo (#46) vs Uzbekistan (#50)',
    'Panama (#33) vs England (#4)', 'Croatia (#11) vs Ghana (#74)'
  ];
  
  headers.push(...fixtures);
  headers.push('Bonus: Pick the game with the earliest card in Matchday 3');
  
  return headers;
}

/**
 * STEP 5: Install triggers for all forms
 * Run this AFTER setting MASTER_SHEET_ID
 */
function installTriggers() {
  if (!MASTER_SHEET_ID) {
    console.log('ERROR: Please set MASTER_SHEET_ID first!');
    return;
  }
  
  console.log('Installing form submission triggers...');
  
  // You'll need to manually get form IDs and update these
  // The forms need to be linked to response spreadsheets first
  
  console.log('Manual step required:');
  console.log('1. Get each form ID from the form URLs');
  console.log('2. Link each form to a response spreadsheet');
  console.log('3. Update the installTriggersWithFormIds() function below with the actual form IDs');
  console.log('4. Run installTriggersWithFormIds()');
}

/**
 * Install triggers with actual form IDs
 * Update the formIds object with actual IDs from your forms
 */
function installTriggersWithFormIds() {
  if (!MASTER_SHEET_ID) {
    console.log('ERROR: Please set MASTER_SHEET_ID first!');
    return;
  }
  
  // UPDATE THESE WITH YOUR ACTUAL FORM IDs
  const formIds = {
    form1: '', // Form 1 ID here
    form2: '', // Form 2 ID here  
    form3: '', // Form 3 ID here
    form4: ''  // Form 4 ID here
  };
  
  // Install triggers
  try {
    ScriptApp.newTrigger('onForm1Submit')
      .create();
    console.log('Trigger installed for Form 1');
    
    ScriptApp.newTrigger('onForm2Submit')
      .create();
    console.log('Trigger installed for Form 2');
    
    ScriptApp.newTrigger('onForm3Submit')
      .create();
    console.log('Trigger installed for Form 3');
    
    ScriptApp.newTrigger('onForm4Submit')
      .create();
    console.log('Trigger installed for Form 4');
    
  } catch (error) {
    console.log('Error installing triggers:', error);
  }
}

/**
 * Form submission handlers
 */
function onForm1Submit(e) {
  copyFormResponseToMaster(e, 'form1_picks');
}

function onForm2Submit(e) {
  copyFormResponseToMaster(e, 'form2_picks');
}

function onForm3Submit(e) {
  copyFormResponseToMaster(e, 'form3_picks');
}

function onForm4Submit(e) {
  copyFormResponseToMaster(e, 'form4_picks');
}

/**
 * Copy form response to master spreadsheet
 */
function copyFormResponseToMaster(e, targetTabName) {
  try {
    if (!MASTER_SHEET_ID) {
      console.log('ERROR: MASTER_SHEET_ID not set');
      return;
    }
    
    const masterSS = SpreadsheetApp.openById(MASTER_SHEET_ID);
    const targetSheet = masterSS.getSheetByName(targetTabName);
    
    if (!targetSheet) {
      console.log(`ERROR: Sheet ${targetTabName} not found`);
      return;
    }
    
    // Get the response data
    const response = e.response;
    const itemResponses = response.getItemResponses();
    
    // Build row data: timestamp + responses
    const rowData = [new Date()]; // timestamp
    
    for (const itemResponse of itemResponses) {
      rowData.push(itemResponse.getResponse());
    }
    
    // Append to master sheet
    targetSheet.appendRow(rowData);
    
    console.log(`Response copied to ${targetTabName}`);
    
  } catch (error) {
    console.log('Error copying response:', error);
  }
}

/**
 * Utility: Backfill existing responses
 * Run this if submissions arrived before triggers were installed
 */
function backfillResponses() {
  console.log('This function would backfill existing responses from individual form response sheets to the master sheet');
  console.log('Implementation depends on your specific form response sheet IDs');
}