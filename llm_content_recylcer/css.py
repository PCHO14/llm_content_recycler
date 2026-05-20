
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

::selection { background: #C1DBE8; color: #43302E; }

/* === Gradio internals === */
:root, .gradio-container {
    --color-orange-500:                  #C1DBE8 !important;
    --color-orange-600:                  #9dc4d8 !important;
    --primary-50:   #FFF1B5 !important;
    --primary-100:  #C1DBE8 !important;
    --primary-200:  #C1DBE8 !important;
    --primary-300:  #9dc4d8 !important;
    --primary-400:  #7aaac8 !important;
    --primary-500:  #43302E !important;
    --primary-600:  #362420 !important;
    --primary-700:  #2a1a18 !important;
    --primary-800:  #1e1210 !important;
    --primary-900:  #120a08 !important;
    --primary-950:  #080402 !important;
    --body-background-fill:              #43302E !important;
    --background-fill-primary:           #43302E !important;
    --background-fill-secondary:         #362420 !important;
    --block-background-fill:             #43302E !important;
    --block-border-color:                #4e3430 !important;
    --block-label-background-fill:       transparent !important;
    --block-label-border-color:          transparent !important;
    --block-label-text-color:            #c9a898 !important;
    --block-title-text-color:            #c9a898 !important;
    --panel-background-fill:             #43302E !important;
    --panel-border-color:                #4e3430 !important;
    --border-color-primary:              #5a3e3a !important;
    --border-color-accent:               #C1DBE8 !important;
    --input-background-fill:             #362420 !important;
    --input-border-color:                #5a3e3a !important;
    --checkbox-background-color:         #362420 !important;
    --checkbox-background-color-selected:#C1DBE8 !important;
    --checkbox-border-color:             #c9a898 !important;
    --checkbox-border-color-selected:    #C1DBE8 !important;
    --button-primary-background-fill:    #C1DBE8 !important;
    --button-primary-text-color:         #43302E !important;
    --button-secondary-background-fill:  transparent !important;
    --button-secondary-text-color:       #c9a898 !important;
    --button-secondary-border-color:     #5a3e3a !important;
    --color-accent:                      #C1DBE8 !important;
    --neutral-50:   #FFF1B5 !important;
    --neutral-100:  #e8d890 !important;
    --neutral-200:  #c9a898 !important;
    --neutral-300:  #a07868 !important;
    --neutral-400:  #7a5048 !important;
    --neutral-500:  #5a3e3a !important;
    --neutral-600:  #4e3430 !important;
    --neutral-700:  #43302E !important;
    --neutral-800:  #362420 !important;
    --neutral-900:  #2a1a18 !important;
    --neutral-950:  #1e1210 !important;
}

* { box-sizing: border-box; }

body, .gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: #43302E !important;
}
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 2.5rem 5rem !important;
}

.gr-box, .gr-form, .gr-panel { box-shadow: none !important; }

/* ХЭДЕР */
.app-header {
    margin-bottom: 2rem; padding-bottom: 1.25rem;
    border-bottom: 1px solid #4e3430;
    display: flex; align-items: baseline; gap: 1rem;
}
.app-header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem; font-weight: 600; color: #FFF1B5;
    letter-spacing: -.02em; margin: 0;
}
.app-header h1 span { color: #C1DBE8; }
.app-header p { font-size: .8rem; color: #c9a898; font-family: 'JetBrains Mono', monospace; margin: 0; }

/* ТАБЫ */
.tab-nav { border-bottom: 1px solid #4e3430 !important; background: transparent !important; gap: 0 !important; }
.tab-nav button {
    font-family: 'JetBrains Mono', monospace !important; font-size: .85rem !important;
    color: #c9a898 !important; border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important; padding: .65rem 1.5rem !important;
    border-radius: 0 !important; transition: all .15s !important; font-weight: 400 !important;
}
.tab-nav button.selected { color: #FFF1B5 !important; border-bottom: 2px solid #C1DBE8 !important; font-weight: 600 !important; }
.tab-nav button:hover:not(.selected) { color: #FFF1B5 !important; }

/* ПОЛЯ ВВОДА */
textarea, input[type="text"] {
    background: #362420 !important; border: 1px solid #5a3e3a !important;
    color: #FFF1B5 !important; border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important; font-size: 1rem !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #C1DBE8 !important; outline: none !important;
    box-shadow: 0 0 0 3px rgba(193,219,232,.15) !important;
}
textarea::placeholder, input::placeholder { color: #c9a898 !important; }

/* ЛЕЙБЛЫ — все одинаковые */
label span, .block label span, label > span,
.gr-form label span, fieldset legend,
.block > label > span, .block-label span,
span.svelte-1gfkn6j, p.svelte-1gfkn6j,
.block-label, .block-label p, .block-label span {
    font-size: .72rem !important; font-weight: 600 !important; color: #c9a898 !important;
    letter-spacing: .08em !important; text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* КНОПКИ PRIMARY */
button.primary, button[class*="primary"] {
    background: #C1DBE8 !important; color: #43302E !important; border: none !important;
    border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: .88rem !important; font-weight: 700 !important;
    padding: .65rem 1.5rem !important; transition: all .15s !important;
}
button.primary:hover, button[class*="primary"]:hover { background: #9dc4d8 !important; color: #43302E !important; }

/* КНОПКИ SECONDARY */
button.secondary, button[class*="secondary"] {
    background: transparent !important; color: #c9a898 !important;
    border: 1px solid #5a3e3a !important; border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: .88rem !important;
}
button.secondary:hover, button[class*="secondary"]:hover { border-color: #C1DBE8 !important; color: #FFF1B5 !important; }

/* БЛОК ПОСТА — полутон коричневого как фильтр */
.md-out {
    background: #4e3430 !important; border: 1px solid #5a3e3a !important;
    border-radius: 6px !important; padding: 1.5rem 1.75rem !important;
    color: #FFF1B5 !important; font-size: 1rem !important; line-height: 1.9 !important;
    min-height: 140px;
}
.md-out h3 { color: #FFF1B5 !important; font-weight: 700 !important; font-size: 1.1rem !important; margin-bottom: .6rem !important; }
.md-out p { color: #FFF1B5 !important; }
.md-out a  { color: #C1DBE8 !important; text-decoration: underline !important; }
.md-out blockquote { border-left: 3px solid #C1DBE8; padding-left: .75rem; color: #c9a898 !important; }
.md-out strong { color: #FFF1B5 !important; }
.md-out em { color: #C1DBE8 !important; }

/* ЛОГ — полутон коричневого как фильтр */
.log-out {
    background: #4e3430 !important; border: 1px solid #5a3e3a !important;
    border-radius: 6px !important; padding: 1.25rem 1.5rem !important;
    color: #FFF1B5 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: .88rem !important; line-height: 1.8 !important; min-height: 140px;
}

/* ПОЖЕЛАНИЯ */
.wishes-box textarea { border-color: #5a3e3a !important; color: #FFF1B5 !important; min-height: 52px !important; }
.wishes-box textarea::placeholder { color: #c9a898 !important; font-style: italic !important; }
.wishes-box textarea:focus { border-color: #C1DBE8 !important; }

/* ЧЕКБОКС */
input[type="checkbox"] {
    appearance: none !important; -webkit-appearance: none !important;
    width: 16px !important; height: 16px !important;
    border: 2px solid #c9a898 !important; border-radius: 3px !important;
    background: #362420 !important; cursor: pointer !important;
    position: relative !important; flex-shrink: 0 !important;
}
input[type="checkbox"]:checked { background: #C1DBE8 !important; border-color: #C1DBE8 !important; }
input[type="checkbox"]:checked::after {
    content: '' !important; position: absolute !important;
    left: 3px !important; top: 0px !important;
    width: 5px !important; height: 9px !important;
    border: 2px solid #43302E !important;
    border-top: none !important; border-left: none !important;
    transform: rotate(45deg) !important; display: block !important;
}

/* РАДИО */
input[type="radio"] {
    appearance: none !important; -webkit-appearance: none !important;
    width: 16px !important; height: 16px !important;
    border: 2px solid #c9a898 !important; border-radius: 50% !important;
    background: #362420 !important; cursor: pointer !important; flex-shrink: 0 !important;
}
input[type="radio"]:checked {
    border-color: #C1DBE8 !important; background: #C1DBE8 !important;
    box-shadow: inset 0 0 0 3px #362420 !important;
}

/* RADIO-BOX — точно как select */
.radio-box, .radio-box > div, .radio-box > div > div {
    background: #4e3430 !important;
    border-radius: 6px !important; border: 1px solid #5a3e3a !important;
    box-shadow: none !important; overflow: hidden !important;
    width: 100% !important; max-width: 100% !important; min-width: 0 !important;
}
.radio-box label, .radio-box span {
    background: transparent !important; border: none !important; box-shadow: none !important;
    white-space: normal !important; word-break: break-word !important;
    width: 100% !important; color: #FFF1B5 !important;
    font-size: .9rem !important; font-family: 'Inter', sans-serif !important;
}
.gr-radio label { padding: .4rem .6rem !important; font-size: .9rem !important; color: #FFF1B5 !important; }
.gr-radio input:checked + label { color: #C1DBE8 !important; font-weight: 600 !important; }
div[data-testid="radio-group"], div[data-testid="radio-group"] > div {
    background: transparent !important; border: none !important; box-shadow: none !important;
}

/* SELECT */
select {
    background: #362420 !important; border: 1px solid #5a3e3a !important;
    color: #FFF1B5 !important; border-radius: 6px !important;
    font-size: .9rem !important; padding: .4rem .6rem !important;
}
select option { background: #43302E !important; color: #FFF1B5 !important; }
select:focus { outline: none !important; border-color: #C1DBE8 !important; }

/* ДРОПДАУН GRADIO */
ul[role="listbox"], ul[role="listbox"] li,
div[role="listbox"], div[role="option"],
.dropdown, .dropdown > div,
div[class*="dropdown"], div[class*="listbox"],
.gr-dropdown, .gr-dropdown ul, .gr-dropdown li {
    background: #43302E !important; background-color: #43302E !important;
    color: #FFF1B5 !important; border-color: #5a3e3a !important;
}
ul[role="listbox"] li:hover, div[role="option"]:hover { background: #5a3e3a !important; color: #FFF1B5 !important; }
ul[role="listbox"] li[aria-selected="true"], div[role="option"][aria-selected="true"] {
    background: #4e3430 !important; color: #C1DBE8 !important;
}

/* ПРОГРЕСС */
.generating { background: transparent !important; border: none !important; }
.progress-bar { background: #362420 !important; border-radius: 3px !important; height: 6px !important; }
.progress-bar > div { background: #C1DBE8 !important; border-radius: 3px !important; }
.generating span { color: #FFF1B5 !important; font-size: .8rem !important; }
.eta-bar { display: none !important; }
progress::-webkit-progress-bar  { background: #362420 !important; border-radius: 3px !important; }
progress::-webkit-progress-value { background: #C1DBE8 !important; border-radius: 3px !important; }
progress::-moz-progress-bar { background: #C1DBE8 !important; }
"""