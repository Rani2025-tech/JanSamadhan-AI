import os
import streamlit as st
from ui_text import ui, supported_languages
from components import esc

def show():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    lang = st.session_state["lang"]

    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="margin: 0; font-size: 1.6rem;">❓ {esc(ui('nav_help', lang))}</h2>
        <p style="margin: 4px 0 0 0; color: var(--muted); font-size: 14.5px;">{esc(ui('help_subtitle', lang))}</p>
    </div>
    """, unsafe_allow_html=True)

    # Section 0: How It Works (Four-Step Process)
    st.markdown(f"""
    <div class="panel-card" style="margin-bottom: 1rem;">
        <h3 style="margin: 0 0 12px 0; font-size: 1.15rem; color: var(--primary);">⚡ {esc(ui('how_it_works', lang))}</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 8px;">
            <div style="background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px;">
                <div style="font-weight: 700; color: var(--primary); font-size: 14px; margin-bottom: 4px;">1. {esc(ui('how_step1_title', lang))}</div>
                <div style="font-size: 13px; color: var(--muted); line-height: 1.4;">{esc(ui('how_step1_desc', lang))}</div>
            </div>
            <div style="background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px;">
                <div style="font-weight: 700; color: var(--primary); font-size: 14px; margin-bottom: 4px;">2. {esc(ui('how_step2_title', lang))}</div>
                <div style="font-size: 13px; color: var(--muted); line-height: 1.4;">{esc(ui('how_step2_desc', lang))}</div>
            </div>
            <div style="background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px;">
                <div style="font-weight: 700; color: var(--primary); font-size: 14px; margin-bottom: 4px;">3. {esc(ui('how_step3_title', lang))}</div>
                <div style="font-size: 13px; color: var(--muted); line-height: 1.4;">{esc(ui('how_step3_desc', lang))}</div>
            </div>
            <div style="background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px;">
                <div style="font-weight: 700; color: var(--primary); font-size: 14px; margin-bottom: 4px;">4. {esc(ui('how_step4_title', lang))}</div>
                <div style="font-size: 13px; color: var(--muted); line-height: 1.4;">{esc(ui('how_step4_desc', lang))}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Section 1: How to File a Complaint
    st.markdown(f"""
    <div class="panel-card" style="margin-bottom: 1rem;">
        <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; color: var(--primary);">📝 {esc(ui('help_how_title', lang))}</h3>
        <p style="margin: 0; font-size: 14.5px; line-height: 1.6;">{esc(ui('help_how_body', lang))}</p>
    </div>
    """, unsafe_allow_html=True)

    # Section 2: What is a Tracking ID?
    st.markdown(f"""
    <div class="panel-card" style="margin-bottom: 1rem;">
        <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; color: var(--primary);">🔍 {esc(ui('help_tracking_title', lang))}</h3>
        <p style="margin: 0; font-size: 14.5px; line-height: 1.6;">{esc(ui('help_tracking_body', lang))}</p>
    </div>
    """, unsafe_allow_html=True)

    # Section 3: Supported Languages
    langs = supported_languages()
    lang_chips_html = []
    for l in langs:
        is_rev = bool(l.get("reviewed"))
        rev_text = esc(ui("reviewed_badge", lang)) if is_rev else esc(ui("machine_translated_badge", lang))
        bg_col = "rgba(63, 163, 77, 0.12)" if is_rev else "rgba(110, 90, 116, 0.12)"
        text_col = "var(--success)" if is_rev else "var(--muted)"
        border_col = "rgba(63, 163, 77, 0.3)" if is_rev else "var(--border)"
        lang_chips_html.append(
            f'<div style="background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; display: flex; align-items: center; justify-content: space-between;">'
            f'  <div><strong style="font-size: 14px;">{esc(l.get("native", ""))}</strong> <span style="color: var(--muted); font-size: 13px;">({esc(l.get("name", ""))})</span></div>'
            f'  <span style="background: {bg_col}; color: {text_col}; border: 1px solid {border_col}; font-size: 11px; padding: 2px 8px; border-radius: 999px; font-weight: 600;">{rev_text}</span>'
            f'</div>'
        )
    chips_joined = "".join(lang_chips_html)

    st.markdown(f"""
    <div class="panel-card" style="margin-bottom: 1rem;">
        <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; color: var(--primary);">🌐 {esc(ui('help_langs_title', lang))}</h3>
        <p style="margin: 0 0 10px 0; font-size: 14.5px; line-height: 1.6;">{esc(ui('help_langs_body', lang))}</p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-bottom: 12px;">
            {chips_joined}
        </div>
        <p style="margin: 8px 0 4px 0; font-size: 13.5px; color: var(--muted); line-height: 1.5;">
            • {esc(ui('help_langs_other_note', lang))}
        </p>
        <p style="margin: 0; font-size: 13.5px; color: var(--muted); line-height: 1.5;">
            • {esc(ui('help_langs_devanagari_note', lang))}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 4: Privacy Notice
    st.markdown(f"""
    <div class="panel-card" style="margin-bottom: 1rem;">
        <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; color: var(--primary);">🛡️ {esc(ui('privacy_title', lang))}</h3>
        <p style="margin: 0; font-size: 14.5px; line-height: 1.6;">{esc(ui('privacy_note', lang))}</p>
    </div>
    """, unsafe_allow_html=True)

    # Section 5: Helpline Contact
    helpline_env = os.getenv("HELPLINE_NUMBER")
    helpline_msg = f"Official Municipal Helpline: {helpline_env}" if helpline_env else ui("help_helpline_unset", lang)

    st.markdown(f"""
    <div class="panel-card" style="border-left: 4px solid var(--primary);">
        <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; color: var(--primary);">📞 {esc(ui('help_helpline_title', lang))}</h3>
        <p style="margin: 0; font-size: 14.5px; line-height: 1.6;">{esc(helpline_msg)}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__" or "st" in globals():
    show()
