# -*- coding: utf-8 -*-
"""
生日照片语音合集二维码生成器
功能：
1. 将指定文件夹中的照片和语音文件生成一个精美的HTML页面
2. 为该页面生成二维码，扫码即可查看照片和语音合集
3. 支持自定义标题、祝福语和背景音乐
"""

import os
import base64
import qrcode
from PIL import Image
import webbrowser

# ==================== 配置区 ====================
PUBLIC_URL = "https://afterglow7777.github.io/surprise1122/"
CONFIG = {
    "title": "乖乖宝贝，生日快乐！",  # 页面标题
    "subtitle": "杨天戈23岁啦",  # 副标题
    "wish_text": "我说有你在的每一天我都很开心，生日快乐，我的小朋友！",  # 祝福语
    "photos_dir": "photos",  # 照片文件夹
    "audio_dir": "audio",  # 语音文件夹
    "output_html": "birthday_surprise.html",  # 生成的HTML文件名
    "output_qr": "birthday_qr.png",  # 二维码图片文件名
    "bg_color": "#FFF0F5",  # 背景色（粉色）
    "card_color": "#FFFFFF",  # 卡片颜色
    "text_color": "#5D3A4A",  # 文字颜色
    "qr_fill_color": "#C2185B",  # 二维码前景色
    "qr_back_color": "#FFFFFF",  # 二维码背景色
}

# 支持的照片和音频扩展名
PHOTO_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
AUDIO_EXTS = ('.mp3', '.wav', '.ogg', '.m4a', '.aac')


# ==================== 工具函数 ====================
def file_to_base64(filepath):
    """将文件转换为base64编码"""
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def get_files(folder, exts):
    """获取文件夹中指定扩展名的文件，按名称排序"""
    if not os.path.isdir(folder):
        return []
    files = []
    for f in os.listdir(folder):
        if f.lower().endswith(exts):
            files.append(os.path.join(folder, f))
    files.sort()
    return files


def build_html(photos, audios, config):
    """生成HTML页面内容（美化版 + 互动版：吹蜡烛后展开照片/语音）
    标题区：礼物盒🎁 + 飘浮星星✨（不再用蛋糕 emoji）
    吹蜡烛区：纯 CSS 插画风蛋糕（分层蛋糕体 + 奶油 + 草莓 + 蜡烛 + 火焰）
    其余互动：吹完展开内容、撒花、爱心迸发、漂浮爱心、点击爱心、灯箱
    媒体文件使用相对路径引用，不再内联 Base64，避免 HTML 过大。"""

    # ---- 照片卡片（使用相对路径） ----
    photo_cards = []
    for p in photos:
        rel_path = p.replace("\\", "/")
        name = os.path.splitext(os.path.basename(p))[0]
        photo_cards.append(f'''
        <figure class="photo-card" data-src="{rel_path}" onclick="openLightbox(this.dataset.src)">
            <img src="{rel_path}" alt="{name}" loading="lazy">
            <figcaption class="caption">{name}</figcaption>
        </figure>''')

    photos_html = "".join(photo_cards) if photo_cards else \
        '<p class="empty-tip">暂无照片，请在 photos 文件夹中添加照片～</p>'

    # ---- 语音卡片（使用相对路径） ----
    audio_cards = []
    for a in audios:
        ext = os.path.splitext(a)[1].lower()
        mime_map = {
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4', '.aac': 'audio/aac'
        }
        mime = mime_map.get(ext, 'audio/mpeg')
        rel_path = a.replace("\\", "/")
        name = os.path.splitext(os.path.basename(a))[0]
        audio_cards.append(f'''
        <div class="audio-card">
            <div class="audio-head">
                <span class="audio-icon">🎙️</span>
                <span class="audio-name">{name}</span>
            </div>
            <audio controls preload="metadata">
                <source src="{rel_path}" type="{mime}">
            </audio>
        </div>''')

    audios_html = "".join(audio_cards) if audio_cards else \
        '<p class="empty-tip">暂无语音，请在 audio 文件夹中添加语音文件～</p>'

    # ---- CSS ----
    css = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
                     "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
        color: #3a2a33;
        line-height: 1.6;
        min-height: 100vh;
        background: #fdf7fa;
        background-image:
            radial-gradient(circle at 15% 0%, #ffe3ee 0%, transparent 45%),
            radial-gradient(circle at 85% 100%, #e9e2ff 0%, transparent 45%);
        -webkit-font-smoothing: antialiased;
        overflow-x: hidden;
    }

    /* 漂浮爱心背景 */
    .floating-hearts {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: 0; overflow: hidden;
    }
    .floating-heart {
        position: absolute; font-size: 1.4rem; opacity: 0;
        animation: floatUp 12s ease-in infinite;
        color: #ffb6c1; user-select: none;
    }
    @keyframes floatUp {
        0% { transform: translateY(100vh) scale(0.6); opacity: 0; }
        10% { opacity: 0.7; }
        90% { opacity: 0.7; }
        100% { transform: translateY(-10vh) scale(1); opacity: 0; }
    }

    .page-wrap { position: relative; z-index: 1; }

    /* ===== 英雄区（礼物盒 + 星星装饰，区别于蛋糕区） ===== */
    .hero {
        text-align: center; padding: 64px 24px 8px; position: relative;
        transition: padding 0.6s ease;
    }
    .hero.compact { padding: 40px 24px 6px; }

    .hero-deco {
        position: relative;
        display: inline-block;
        width: 124px; height: 88px;
        margin-bottom: 2px;
    }
    .gift-emoji {
        position: absolute; left: 50%; top: 50%;
        transform: translate(-50%, -50%);
        font-size: 56px; line-height: 1;
        animation: giftBounce 2.6s ease-in-out infinite;
        filter: drop-shadow(0 8px 14px rgba(230, 100, 150, 0.28));
        transition: font-size 0.6s ease;
    }
    .hero.compact .gift-emoji { font-size: 44px; }

    @keyframes giftBounce {
        0%, 100% { transform: translate(-50%, -50%) rotate(-4deg) scale(1); }
        50% { transform: translate(-50%, -62%) rotate(4deg) scale(1.06); }
    }

    .spark {
        position: absolute;
        font-size: 15px;
        opacity: 0.85;
        animation: twinkle 2.2s ease-in-out infinite;
        user-select: none;
    }
    .spark.s1 { left: 2px; top: 8px; animation-delay: 0s; }
    .spark.s2 { right: 0px; top: 16px; animation-delay: 0.5s; }
    .spark.s3 { left: 14px; bottom: 2px; animation-delay: 1s; }
    .spark.s4 { right: 12px; bottom: 8px; animation-delay: 1.5s; }

    @keyframes twinkle {
        0%, 100% { transform: scale(0.7) rotate(0deg); opacity: 0.35; }
        50% { transform: scale(1.15) rotate(20deg); opacity: 0.95; }
    }

    .hero h1 {
        font-size: clamp(1.8rem, 5.5vw, 3rem);
        font-weight: 800; letter-spacing: 0.02em; margin: 10px 0 6px;
        background: linear-gradient(135deg, #e75480, #b83b5e, #9b3a6a);
        -webkit-background-clip: text; background-clip: text;
        color: transparent; background-size: 200% 200%;
        animation: gradientShift 4s ease infinite;
    }
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    .subtitle { color: #8a6a78; font-size: 1.05rem; letter-spacing: 0.04em; }

    .wish {
        display: inline-block; margin-top: 22px; padding: 12px 30px;
        border-radius: 999px; color: #fff; font-size: 1rem; font-weight: 500;
        background: linear-gradient(135deg, #f06d9a, #c94b7a);
        box-shadow: 0 8px 22px rgba(201, 75, 122, 0.32);
        position: relative; overflow: hidden;
    }
    .wish::after {
        content: ''; position: absolute; top: -50%; left: -60%;
        width: 40%; height: 200%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transform: rotate(25deg); animation: shimmer 3.5s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% { left: -60%; }
        50% { left: 120%; }
    }

    /* ===== 互动区：吹蜡烛 ===== */
    .interact-section {
        max-width: 720px; margin: 30px auto 0; padding: 0 20px;
        transition: opacity 0.6s ease, transform 0.6s ease, margin 0.6s ease;
    }
    .interact-section.done {
        opacity: 0.9;
        transform: scale(0.98);
    }

    .cake-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border-radius: 30px; padding: 26px 24px 24px; text-align: center;
        box-shadow: 0 14px 44px rgba(200, 80, 130, 0.16);
        border: 1px solid rgba(255, 200, 220, 0.55);
        position: relative; overflow: hidden;
    }
    .cake-card::before {
        content: ''; position: absolute; top: -70px; left: 50%;
        transform: translateX(-50%);
        width: 260px; height: 140px; border-radius: 50%;
        background: radial-gradient(circle, rgba(255, 214, 230, 0.75), transparent 70%);
        pointer-events: none;
    }

    .cake-card h3 {
        font-size: 1.12rem; color: #b04070; margin-bottom: 6px;
        font-weight: 700; position: relative;
    }
    .cake-card .hint {
        font-size: 0.85rem; color: #a88a96; margin-bottom: 16px; position: relative;
    }

    /* ===== CSS 插画风蛋糕 ===== */
    .cake-scene {
        position: relative;
        width: 200px; height: 196px;
        margin: 0 auto;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
        user-select: none;
        transition: transform 0.2s ease;
    }
    .cake-scene:active { transform: scale(0.97); }

    .plate {
        position: absolute; left: 50%; bottom: 6px;
        transform: translateX(-50%);
        width: 168px; height: 20px; border-radius: 50%;
        background: radial-gradient(ellipse at 50% 40%, #ffffff, #f3d9e4 70%, #e9c3d3);
        box-shadow: 0 8px 18px rgba(190, 100, 140, 0.22);
        z-index: 1;
    }

    .cake-layer {
        position: absolute; left: 50%; transform: translateX(-50%);
        border-radius: 10px 10px 8px 8px;
        z-index: 2;
    }
    .layer-bottom {
        bottom: 18px; width: 148px; height: 46px;
        background: linear-gradient(180deg, #f7b9d0, #e98cb2);
        box-shadow: inset 0 -6px 0 rgba(180, 70, 120, 0.18);
    }
    .layer-top {
        bottom: 62px; width: 120px; height: 36px;
        background: linear-gradient(180deg, #ffd1e2, #f7a9c8);
        box-shadow: inset 0 -5px 0 rgba(180, 70, 120, 0.14);
    }

    .cream {
        position: absolute; left: 50%; transform: translateX(-50%);
        height: 16px; border-radius: 12px;
        background: linear-gradient(180deg, #ffffff, #ffeaf2);
        box-shadow: 0 2px 6px rgba(220, 150, 180, 0.25);
        z-index: 3;
    }
    .cream.c1 { bottom: 58px; width: 150px; }
    .cream.c2 { bottom: 94px; width: 122px; }

    .cream-drip {
        position: absolute; left: 50%; transform: translateX(-50%);
        width: 150px; height: 14px; bottom: 52px;
        z-index: 4;
        background:
            radial-gradient(circle at 8px 0, #ffffff 7px, transparent 8px) 0 0/20px 14px repeat-x;
    }

    .berry {
        position: absolute; width: 16px; height: 16px;
        background: radial-gradient(circle at 35% 30%, #ff6b81, #d81b4a);
        border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
        box-shadow: 0 2px 5px rgba(190, 30, 70, 0.35);
        z-index: 5;
    }
    .berry::after {
        content: ''; position: absolute; top: -4px; left: 50%;
        transform: translateX(-50%);
        width: 8px; height: 6px; border-radius: 50% 50% 0 0;
        background: #4caf50;
    }
    .berry.b1 { left: 30px; bottom: 96px; }
    .berry.b2 { right: 30px; bottom: 96px; }
    .berry.b3 { left: 62px; bottom: 60px; }
    .berry.b4 { right: 62px; bottom: 60px; }

    .candle {
        position: absolute; left: 50%; bottom: 128px;
        transform: translateX(-50%);
        width: 14px; height: 36px; border-radius: 4px;
        background: repeating-linear-gradient(
            180deg,
            #ff8fab 0 6px,
            #ffffff 6px 12px
        );
        box-shadow: 0 2px 6px rgba(190, 80, 120, 0.25);
        z-index: 6;
    }
    .candle::after {
        content: ''; position: absolute; top: -5px; left: 50%;
        transform: translateX(-50%);
        width: 2px; height: 6px; background: #7a4a58; border-radius: 2px;
    }

    .candle-flame {
        position: absolute; left: 50%; bottom: 164px;
        transform: translateX(-50%);
        width: 16px; height: 24px;
        background: radial-gradient(circle at 50% 70%, #fff3b0 0%, #ffd54f 35%, #ff9800 70%, #ff5722 100%);
        border-radius: 50% 50% 50% 50% / 65% 65% 35% 35%;
        box-shadow: 0 0 18px 6px rgba(255, 170, 60, 0.45);
        transform-origin: 50% 100%;
        animation: flameFlicker 0.55s ease-in-out infinite alternate;
        z-index: 7;
        transition: opacity 0.4s ease, transform 0.4s ease;
    }
    @keyframes flameFlicker {
        0% { transform: translateX(-50%) scale(1) rotate(-3deg); }
        100% { transform: translateX(-50%) scale(1.1, 1.18) rotate(3deg); }
    }
    .candle-flame.out {
        opacity: 0;
        transform: translateX(-50%) scale(0.3);
        animation: none;
    }

    .flame-glow {
        position: absolute; left: 50%; bottom: 150px;
        transform: translateX(-50%);
        width: 90px; height: 90px; border-radius: 50%;
        background: radial-gradient(circle, rgba(255, 200, 90, 0.35), transparent 65%);
        z-index: 0;
        transition: opacity 0.5s ease;
        pointer-events: none;
    }
    .flame-glow.out { opacity: 0; }

    .smoke {
        position: absolute; left: 50%; bottom: 168px;
        transform: translateX(-50%);
        font-size: 16px; opacity: 0;
        transition: opacity 0.4s ease;
        pointer-events: none; z-index: 8;
    }
    .smoke.show { opacity: 0.75; animation: smokeRise 1.9s ease-out forwards; }
    @keyframes smokeRise {
        0% { transform: translateX(-50%) translateY(0) scale(0.8); opacity: 0.75; }
        100% { transform: translateX(-50%) translateY(-52px) scale(1.7); opacity: 0; }
    }

    .blow-btn {
        margin-top: 18px; display: inline-flex; align-items: center; gap: 8px;
        padding: 12px 30px; border: none; border-radius: 999px;
        font-size: 0.96rem; font-weight: 600; color: #fff;
        background: linear-gradient(135deg, #ff7e9d, #e75480);
        box-shadow: 0 8px 20px rgba(231, 84, 128, 0.38);
        cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease;
        -webkit-tap-highlight-color: transparent; font-family: inherit;
        position: relative;
    }
    .blow-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(231, 84, 128, 0.48); }
    .blow-btn:active { transform: scale(0.96); }
    .blow-btn:disabled {
        opacity: 0.55; cursor: default; transform: none;
        box-shadow: 0 6px 18px rgba(231, 84, 128, 0.2);
    }

    .blessing-msg {
        margin-top: 14px; font-size: 0.95rem; font-weight: 600;
        color: #c94b7a; min-height: 1.4em; transition: opacity 0.4s ease;
        position: relative;
    }

    /* ===== 内容区（吹蜡烛后显示） ===== */
    .content-section {
        max-width: 1080px; margin: 0 auto; padding: 0 20px;
        max-height: 0; opacity: 0; overflow: hidden;
        transform: translateY(60px);
        transition: max-height 1.2s cubic-bezier(0.22, 1, 0.36, 1),
                    opacity 0.9s ease 0.15s,
                    transform 0.9s cubic-bezier(0.22, 1, 0.36, 1) 0.15s;
        pointer-events: none;
    }
    .content-section.open {
        max-height: 12000px; opacity: 1; transform: none;
        pointer-events: auto;
    }

    .section-title {
        display: flex; align-items: center; gap: 10px;
        font-size: 1.25rem; font-weight: 700; margin: 48px 0 20px; color: #4a2f3c;
    }
    .section-title::before {
        content: ''; width: 4px; height: 20px; border-radius: 2px;
        background: linear-gradient(#e75480, #b83b5e);
    }

    .gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 18px;
    }

    .photo-card {
        background: #fff; border-radius: 18px; overflow: hidden;
        box-shadow: 0 6px 20px rgba(180, 60, 110, 0.08);
        transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease,
                    opacity 0.6s ease;
        cursor: pointer; position: relative;
        opacity: 0;
        transform: translateY(30px) scale(0.96);
    }
    .photo-card.show {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
    .photo-card.show:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 16px 36px rgba(180, 60, 110, 0.22);
    }

    .photo-card img {
        width: 100%; aspect-ratio: 1 / 1; object-fit: cover;
        display: block; transition: transform 0.5s ease;
    }
    .photo-card.show:hover img { transform: scale(1.06); }

    .caption {
        padding: 10px 12px; font-size: 0.85rem; color: #7a5a68;
        text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    .audio-card {
        background: #fff; border-radius: 18px; padding: 16px 18px; margin-bottom: 16px;
        box-shadow: 0 6px 20px rgba(180, 60, 110, 0.08);
        transition: box-shadow 0.3s ease, opacity 0.6s ease, transform 0.6s ease;
        opacity: 0;
        transform: translateY(24px);
    }
    .audio-card.show {
        opacity: 1;
        transform: none;
    }
    .audio-card.show:hover { box-shadow: 0 10px 28px rgba(180, 60, 110, 0.14); }

    .audio-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .audio-icon { font-size: 1.15rem; }
    .audio-name { font-weight: 600; font-size: 0.95rem; color: #5a3a48; }
    .audio-card audio { width: 100%; height: 40px; border-radius: 8px; }

    .empty-tip {
        text-align: center; padding: 30px; opacity: 0.5;
        font-style: italic; font-size: 0.92rem;
    }

    /* ===== 页脚 ===== */
    .footer {
        text-align: center; padding: 60px 20px 44px;
        color: #a88a96; font-size: 0.9rem;
    }
    .footer .heart {
        color: #e75480; display: inline-block;
        animation: heartBeat 1.4s ease-in-out infinite;
    }
    @keyframes heartBeat {
        0%, 100% { transform: scale(1); }
        15% { transform: scale(1.3); }
        30% { transform: scale(1); }
        45% { transform: scale(1.2); }
    }

    /* ===== 灯箱 ===== */
    .lightbox {
        display: none; position: fixed; inset: 0;
        background: rgba(20, 10, 15, 0.92);
        -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
        z-index: 9999; padding: 24px;
        align-items: center; justify-content: center; cursor: zoom-out;
    }
    .lightbox.active { display: flex; }
    .lightbox img {
        max-width: 92vw; max-height: 88vh; border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        animation: zoom 0.3s ease;
    }
    @keyframes zoom {
        from { transform: scale(0.92); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }

    /* 撒花彩带 */
    .confetti-piece {
        position: fixed; width: 10px; height: 10px; z-index: 9998;
        pointer-events: none; border-radius: 2px;
        animation: confettiFall linear forwards;
    }
    @keyframes confettiFall {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(110vh) rotate(720deg); opacity: 0.3; }
    }

    /* 点击爱心 */
    .pop-heart {
        position: fixed; pointer-events: none; z-index: 9998; font-size: 1.6rem;
        animation: popHeart 0.9s ease-out forwards;
    }
    @keyframes popHeart {
        0% { transform: translate(-50%, -50%) scale(0.5); opacity: 1; }
        100% { transform: translate(-50%, -120%) scale(1.8); opacity: 0; }
    }

    @media (max-width: 560px) {
        .hero { padding: 52px 20px 4px; }
        .hero.compact { padding: 32px 20px 2px; }
        .hero-deco { width: 108px; height: 78px; }
        .gift-emoji { font-size: 48px; }
        .hero.compact .gift-emoji { font-size: 38px; }
        .gallery { grid-template-columns: repeat(2, 1fr); gap: 12px; }
        .caption { font-size: 0.75rem; padding: 8px 6px; }
        .section-title { margin: 36px 0 16px; font-size: 1.15rem; }
        .interact-section { margin-top: 24px; }
        .cake-card { padding: 22px 16px 20px; }
        .cake-scene { width: 176px; height: 172px; }
        .plate { width: 150px; }
        .layer-bottom { width: 132px; }
        .layer-top { width: 108px; }
        .cream.c1 { width: 134px; }
        .cream.c2 { width: 110px; }
        .cream-drip { width: 134px; }
        .berry.b1 { left: 24px; }
        .berry.b2 { right: 24px; }
        .berry.b3 { left: 52px; }
        .berry.b4 { right: 52px; }
    }
    """

    # ---- JS ----
    js = """
    function openLightbox(src) {
        var lb = document.getElementById('lightbox');
        document.getElementById('lightbox-img').src = src;
        lb.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    function closeLightbox() {
        document.getElementById('lightbox').classList.remove('active');
        document.body.style.overflow = '';
    }
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeLightbox();
    });

    /* ===== 吹蜡烛互动（吹完后展开内容区） ===== */
    var candleBlown = false;
    function blowCandles() {
        if (candleBlown) return;
        candleBlown = true;

        var flame = document.getElementById('candleFlame');
        var smoke = document.getElementById('smoke');
        var glow = document.getElementById('flameGlow');
        var btn = document.getElementById('blowBtn');
        var msg = document.getElementById('blessingMsg');
        var hero = document.getElementById('hero');
        var interact = document.getElementById('interactSection');
        var content = document.getElementById('contentSection');

        flame.classList.add('out');
        glow.classList.add('out');
        smoke.classList.add('show');
        btn.disabled = true;
        btn.innerHTML = '<span>🎉</span> 已许愿';
        msg.textContent = '✨ 愿望已经许下啦，一定会实现的！✨';

        spawnConfetti();
        spawnHeartBurst();

        hero.classList.add('compact');
        interact.classList.add('done');

        setTimeout(function () {
            content.classList.add('open');
            revealCards();
            setTimeout(function () {
                content.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 500);
        }, 900);
    }

    function revealCards() {
        var photos = document.querySelectorAll('.photo-card');
        var audios = document.querySelectorAll('.audio-card');
        var all = [];
        photos.forEach(function (el) { all.push(el); });
        audios.forEach(function (el) { all.push(el); });
        all.forEach(function (el, i) {
            setTimeout(function () { el.classList.add('show'); }, i * 110);
        });
    }

    function spawnConfetti() {
        var colors = ['#e75480', '#ffb6c1', '#ffd700', '#c94b7a', '#b83b5e', '#f3b8cd', '#fff0f5', '#e9e2ff'];
        for (var i = 0; i < 70; i++) {
            var piece = document.createElement('div');
            piece.className = 'confetti-piece';
            var size = Math.random() * 8 + 6;
            piece.style.width = size + 'px';
            piece.style.height = size * (Math.random() * 0.6 + 0.6) + 'px';
            piece.style.left = Math.random() * 100 + 'vw';
            piece.style.top = '-10vh';
            piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
            piece.style.animationDuration = (Math.random() * 1.8 + 1.8) + 's';
            piece.style.animationDelay = (Math.random() * 0.6) + 's';
            document.body.appendChild(piece);
            setTimeout((function (el) {
                return function () { el.remove(); };
            })(piece), 5000);
        }
    }

    function spawnHeartBurst() {
        var emojis = ['❤️', '💖', '💕', '💗', '💝', '🌸', '✨', '🎉'];
        var scene = document.getElementById('cakeScene');
        var rect = scene.getBoundingClientRect();
        var cx = rect.left + rect.width / 2;
        var cy = rect.top + rect.height / 2;
        for (var i = 0; i < 14; i++) {
            var heart = document.createElement('div');
            heart.className = 'pop-heart';
            heart.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            heart.style.left = (cx + (Math.random() - 0.5) * 160) + 'px';
            heart.style.top = (cy + (Math.random() - 0.5) * 100) + 'px';
            heart.style.fontSize = (Math.random() * 16 + 14) + 'px';
            heart.style.animationDelay = (Math.random() * 0.3) + 's';
            document.body.appendChild(heart);
            setTimeout((function (el) {
                return function () { el.remove(); };
            })(heart), 1400);
        }
    }

    function initFloatingHearts() {
        var container = document.getElementById('floatingHearts');
        var hearts = ['❤️', '💖', '💕', '💗', '🌸', '✨', '💝'];
        for (var i = 0; i < 16; i++) {
            var el = document.createElement('div');
            el.className = 'floating-heart';
            el.textContent = hearts[Math.floor(Math.random() * hearts.length)];
            el.style.left = Math.random() * 100 + 'vw';
            el.style.fontSize = (Math.random() * 14 + 12) + 'px';
            el.style.animationDuration = (Math.random() * 8 + 10) + 's';
            el.style.animationDelay = (Math.random() * 10) + 's';
            container.appendChild(el);
        }
    }

    function initClickHeart() {
        document.addEventListener('click', function (e) {
            if (e.target.closest('button, audio, .lightbox, .blow-btn, .cake-scene')) return;
            var heart = document.createElement('div');
            heart.className = 'pop-heart';
            heart.textContent = ['❤️', '💖', '💕', '✨'][Math.floor(Math.random() * 4)];
            heart.style.left = e.clientX + 'px';
            heart.style.top = e.clientY + 'px';
            heart.style.fontSize = (Math.random() * 12 + 16) + 'px';
            document.body.appendChild(heart);
            setTimeout((function (el) {
                return function () { el.remove(); };
            })(heart), 1000);
        });
    }

    function init() {
        initFloatingHearts();
        initClickHeart();
        document.getElementById('blowBtn').addEventListener('click', function (e) {
            e.stopPropagation();
            blowCandles();
        });
        document.getElementById('cakeScene').addEventListener('click', function (e) {
            e.stopPropagation();
            blowCandles();
        });
        document.getElementById('cakeScene').addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                blowCandles();
            }
        });
    }

    document.addEventListener('DOMContentLoaded', init);
    """

    # ---- 组装 HTML ----
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{config['title']}</title>
    <style>{css}</style>
</head>
<body>
    <div class="floating-hearts" id="floatingHearts"></div>

    <div class="page-wrap">

        <!-- 英雄区：礼物盒 + 星星装饰（与蛋糕区区分） -->
        <header class="hero" id="hero">
            <div class="hero-deco">
                <span class="spark s1">✨</span>
                <span class="spark s2">⭐</span>
                <span class="spark s3">💫</span>
                <span class="spark s4">✨</span>
                <span class="gift-emoji">🎁</span>
            </div>
            <h1>{config['title']}</h1>
            <p class="subtitle">{config['subtitle']}</p>
            <div class="wish">💝 {config['wish_text']}</div>
        </header>

        <!-- 互动区：CSS 插画风蛋糕 -->
        <section class="interact-section" id="interactSection">
            <div class="cake-card">
                <h3>🎈 许个愿吧</h3>
                <p class="hint">点击蛋糕或按钮吹灭蜡烛～</p>
                <div class="cake-scene" id="cakeScene" role="button" tabindex="0" aria-label="点击吹蜡烛">
                    <div class="flame-glow" id="flameGlow"></div>
                    <div class="plate"></div>
                    <div class="cake-layer layer-bottom"></div>
                    <div class="cake-layer layer-top"></div>
                    <div class="cream c1"></div>
                    <div class="cream c2"></div>
                    <div class="cream-drip"></div>
                    <div class="berry b1"></div>
                    <div class="berry b2"></div>
                    <div class="berry b3"></div>
                    <div class="berry b4"></div>
                    <div class="candle"></div>
                    <div class="candle-flame" id="candleFlame"></div>
                    <div class="smoke" id="smoke">💨</div>
                </div>
                <div>
                    <button class="blow-btn" id="blowBtn" type="button">
                        <span>💨</span> 吹蜡烛
                    </button>
                </div>
                <p class="blessing-msg" id="blessingMsg"></p>
            </div>
        </section>

        <!-- 内容区：吹蜡烛后展开 -->
        <main class="content-section" id="contentSection">
            <h2 class="section-title">我们的照片</h2>
            <div class="gallery">
                {photos_html}
            </div>

            <h2 class="section-title">想对你说的话</h2>
            <div class="audio-list">
                {audios_html}
            </div>

            <footer class="footer">
                <p>涵涵<span class="heart">❤</span>杨天戈</p>
                <p>生日快乐，我的宝贝</p>
            </footer>
        </main>

    </div>

    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <img id="lightbox-img" src="" alt="preview">
    </div>

    <script>{js}</script>
</body>
</html>'''
    return html


def generate_qr(data, output_path, fill_color, back_color):
    """生成二维码，内容为data（这里为HTML文件路径或URL）"""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img.save(output_path)
    return output_path


# ==================== 主流程 ====================
def main():
    print("=" * 50)
    print("🎂 生日照片语音合集二维码生成器 🎂")
    print("=" * 50)

    # 1. 读取文件
    photos = get_files(CONFIG['photos_dir'], PHOTO_EXTS)
    audios = get_files(CONFIG['audio_dir'], AUDIO_EXTS)

    print(f"\n📸 找到 {len(photos)} 张照片")
    for p in photos: print(f"   - {os.path.basename(p)}")
    print(f"🎤 找到 {len(audios)} 个语音文件")
    for a in audios: print(f"   - {os.path.basename(a)}")

    if not photos and not audios:
        print("\n⚠️  警告：photos 和 audio 文件夹中都没有文件！")
        print("   请先创建文件夹并放入照片/语音后再运行。")
        print("   程序将继续生成空页面，但建议添加内容。")

    # 2. 构建HTML
    print("\n🔨 正在生成HTML页面...")
    html_content = build_html(photos, audios, CONFIG)
    with open(CONFIG['output_html'], 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ HTML已生成：{CONFIG['output_html']}")

    # 3. 生成二维码
    if PUBLIC_URL.strip():
        qr_data = PUBLIC_URL.strip()
        print(f"\n🌐 使用公网地址生成二维码：{qr_data}")
    else:
        abs_path = os.path.abspath(CONFIG['output_html'])
        qr_data = "file://" + abs_path.replace("\\", "/")
        print("\n⚠️  未设置 PUBLIC_URL，二维码只能在本机打开。")

    print(f"\n📱 正在生成二维码...")
    print(f"   二维码内容（文件路径）：{qr_data}")
    qr_path = generate_qr(qr_data, CONFIG['output_qr'],
                          CONFIG['qr_fill_color'], CONFIG['qr_back_color'])
    print(f"✅ 二维码已生成：{CONFIG['output_qr']}")

    # 4. 完成提示
    print("\n" + "=" * 50)
    print("🎉 全部完成！")
    print("=" * 50)
    print(f"\n📄 页面文件：{os.path.abspath(CONFIG['output_html'])}")
    print(f"📱 二维码文件：{os.path.abspath(CONFIG['output_qr'])}")
    print("\n💡 使用说明：")
    print("   1. 将 HTML 文件和二维码图片一起发送给男朋友")
    print("   2. 他扫码后，用浏览器打开即可查看照片和听语音")
    print("   3. 如果手机无法直接打开file://路径，建议：")
    print("      - 将HTML文件上传到网盘/服务器，重新生成二维码指向URL")
    print("      - 或使用微信/QQ等发送HTML文件，用浏览器打开后分享")
    print("\n💕 祝你的男朋友生日快乐！")

    # 5. 自动打开预览（可选）
    try:
        webbrowser.open(f"file://{abs_path}")
    except:
        pass


if __name__ == "__main__":
    main()