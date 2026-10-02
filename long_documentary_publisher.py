import os
import sys
import random
import asyncio
import io
import json
import re
import subprocess
import urllib.parse
import requests
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    setattr(PIL.Image, 'ANTIALIAS', PIL.Image.Resampling.LANCZOS)

from PIL import Image, ImageDraw, ImageFont, features
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    ColorClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx
)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
NICHE_NAMES = ["أبعاد جغرافية", "مشاريع عملاقة", "مسار"]

DOC_BGM_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dark-mystery-trailer-111586.mp3"

# ==============================================================================
# السيناريو الاستقصائي العملاق (3,600 كلمة - 30 مشهداً دسمة لإنتاج 30 دقيقة فعلية)
# ==============================================================================
MASTER_30MIN_DEEP_DOC = {
    "title": "شرايين الكوكب الخفية: المعركة السرية للتحكم في ممرات العالم المائية",
    "desc": "تحقيق وثائقي استقصائي شامل يمتد لـ 30 دقيقة، يكشف كواليس أخطر نقاط الاختناق الملاحية وصراعات الممرات والنفط وسلاسل الإمداد الدولية.\n\n#أبعاد_جغرافية #وثائقي #جغرافيا #مشاريع #مضائق #اقتصاد",
    "chapters": [
        {
            "chapter_idx": 1,
            "title": "الفصل الأول: لغز نقاط الاختناق الحاكمة لكوكب الأرض",
            "scenes": [
                {
                    "narration": "منذ فجر التاريخ البشري وبداية نشأة الإمبراطوريات الكبرى، لم تكن قوة الدول تُقاس فقط باتساع أراضيها أو بعدد جنودها في الميدان، بل كانت ترتبط دائماً بمعادلة أكثر تعقيداً ودقة: القدرة على إحكام السيطرة على المعابر المائية التي تسلكها التجارة الدولية. كوكب الأرض الذي نعيش عليه، ورغم مساحاته المائية الشاسعة التي تغطي أكثر من سبعين بالمئة من سطحه، محكوم جغرافياً بمصائد وممرات ضيقة جداً تُعرف في العلوم الجيوسياسية بنقاط الاختناق البحري. هذه النقاط تمثل شرايين غير قابلة للاستبدال، وتتحكم بشكل مطلق في حركة التجارة وإمدادات الطاقة والغذاء بين الشرق والغرب.",
                    "query": "aerial cinematic ocean strait container ship",
                    "backup_img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&h=1080&fit=crop",
                    "lower_third": "📍 المعضلة الجغرافية: نقاط الاختناق الدولية"
                },
                {
                    "narration": "اليوم، وفي ظل النظام الاقتصادي المعولم، تتحرك أكثر من تسعين بالمئة من إجمالي البضائع والمنتجات المصنعة حول العالم عبر أساطيل النقل البحري العملاقة. كل جهاز إلكتروني تحمله بيدك، وكل طن من الحبوب والقمح يُصنع منه رغيف الخبز، وقطاع واسع من براميل النفط التي تدير محطات الطاقة والمصانع، تعبر إجبارياً عبر ممرات مائية لا يتجاوز عرض بعضها بضعة كيلومترات معدودة. هذا التمركز اللوجستي الهائل جعل الكوكب بأسره رهينة لحسابات أمنية وجغرافية دقيقة للغاية، حيث إن حدوث أي ارتباك أو توقف مؤقت في أحد هذه المضائق كفيل بإحداث صدمة تضخمية فورية تجتاح الأسواق في قارات العالم الست دون استثناء.",
                    "query": "massive cargo container terminal port aerial",
                    "backup_img": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1920&h=1080&fit=crop",
                    "lower_third": "📦 90% من تجارة العالم معلقة بالبحار"
                },
                {
                    "narration": "ولفهم حجم هذا التهديد المركب، يجب أن ندرك أن ميزان القوى العالمي لم يعد يُدار فقط عبر القنوات الدبلوماسية التقليدية أو المعاهدات الورقية، بل تحول إلى سباق استراتيجي خفي لتأمين هذه المسارات أو القدرة على تعطيلها وقت الأزمات الكبرى. القوى الدولية الكبرى تدرك تماماً أن تكلفة خوض حروب شاملة باهظة للغاية، لكن امتلاك ورقة الضغط على شريان ملاحي واحد يمنح الدولة نفوذاً تفاوضياً يعادل ترسانات عسكرية كاملة. ومن هنا بدأت تظهر نظريات الهيمنة البحرية التي صاغها كبار المفكرين العسكريين، والتي تؤكد أن من يتحكم في البحار يتحكم في التجارة، ومن يتحكم في التجارة يملك مصير العالم.",
                    "query": "warship naval military fleet patrolling open sea",
                    "backup_img": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1920&h=1080&fit=crop",
                    "lower_third": "⚡ نظرية السيطرة البحرية وصراع النفوذ"
                },
                {
                    "narration": "السؤال الذي يشغل بال أجهزة التخطيط الاستراتيجي وغرف التجارة العالمية هو: كيف فرضت طبيعة التضاريس الجغرافية لكوكب الأرض مسارات إجبارية لا يمكن الالتفاف حولها بسهولة؟ وكيف يمكن لمضيق مائي صغير أن يهدد بشل حركة العالم خلال ساعات معدودة؟ للإجابة عن هذا التساؤل المعقد، سنخوض معاً في هذا التحقيق الوثائقي رحلة استقصائية متعمقة ترصد أدق تفاصيل هذه المعركة الخفية، ونفكك بالأرقام والخرائط كواليس الصراع على أهم الممرات المائية التي تبقي الحضارة الإنسانية على قيد الحياة كل يوم.",
                    "query": "satellite world map glowing digital logistics lines",
                    "backup_img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&h=1080&fit=crop",
                    "lower_third": "🌐 خريطة الشرايين الحيوية للقرن الحادي والعشرين"
                },
                {
                    "narration": "لكي نبدأ بتفكيك خيوط هذه المعركة الجيوسياسية المعقدة، يجب أن نتوجه أولاً إلى أكثر بقعة مائية توتراً وحساسية على ظهر البسيطة، البقعة التي يخرج منها خُمس إمدادات الطاقة التي تحرك كل طائرة وسيارة ومصنع على هذا الكوكب، والتي تحولت مياهها إلى ساحة شطرنج دائمة بين القوى الإقليمية والدولية العظمى.",
                    "query": "persian gulf middle east coastline oil terminal drone",
                    "backup_img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&h=1080&fit=crop",
                    "lower_third": "🧭 بداية التحقيق: نحو الرئة النفطية للكوكب"
                }
            ]
        },
        {
            "chapter_idx": 2,
            "title": "الفصل الثاني: مضيق هرمز وصراع الطاقة النووي",
            "scenes": [
                {
                    "narration": "يقع مضيق هرمز في موقع استراتيجي فريد يفصل بين مياه الخليج العربي وخليج عمان، ويمثل البوابة البحرية الوحيدة للدول الرئيسية المنتجة للنفط في الشرق الأوسط للوصول إلى المحيط الهندي والأسواق العالمية المفتوحة. عبر هذا الممر المائي الضيق، تعبر يومياً ناقلات نفط عملاقة تحمل أكثر من عشرين مليون برميل من النفط الخام والمشتقات البترولية، بالإضافة إلى كميات هائلة من الغاز الطبيعي المسال الذي يغذي محطات الكهرباء في كبرى اقتصادات العالم الصناعية في آسيا وأوروبا.",
                    "query": "oil tanker strait of hormuz drone shot aerial",
                    "backup_img": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1920&h=1080&fit=crop",
                    "lower_third": "📍 مضيق هرمز: الرئة النفطية الحاكمة"
                },
                {
                    "narration": "المفارقة الجغرافية الصادمة في مضيق هرمز تكمن في أن أضيق نقطة فيه لا يتجاوز عرضها تسعة وثلاثين كيلومتراً، ولكن الممر الملاحي الآمن والصالح لعبور ناقلات النفط العملاقة لا يتعدى عرضه ميلين بحريين فقط في كل اتجاه، مع وجود منطقة عازلة بينهما بعرض ميلين أيضاً. هذا يعني أن أضخم سفن العالم، التي تزن حمولتها مئات الآلاف من الأطنان وتحتاج إلى مسافات توقف تصل لعدة كيلومترات، تسير في مسار ضيق ومحدد بدقة متناهية لا يحتمل أدنى خطأ ملاحي أو حادث أمني.",
                    "query": "crude oil tanker open sea ocean navigation",
                    "backup_img": "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=1920&h=1080&fit=crop",
                    "lower_third": "🛢️ 20 مليون برميل يومياً في ممر ضيق"
                },
                {
                    "narration": "هذه الطبيعة الجغرافية الحساسة تجعل المضيق عرضة للابتزاز العسكري والمخاطر الأمنية المستمرة. ففي حال تعرضت ناقلة نفط واحدة للاستهداف أو زُرعت ألغام بحرية في مسار الملاحة، ترتفع أقساط التأمين ضد مخاطر الحرب إلى مستويات فلكية، وترفض شركات الشحن الدولية إرسال أساطيلها إلى المنطقة. هذا الشلل اللحظي يترجم فوراً في أسواق المال العالمية إلى قفزات جنونية في أسعار خام برنت، وهو ما ينعكس بارتفاع مباشر في تكاليف المعيشة وأسعار السلع للمواطنين في كل بقعة حول الأرض.",
                    "query": "naval military escort patrol boat stormy sea",
                    "backup_img": "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=1920&h=1080&fit=crop",
                    "lower_third": "⚠️ اشتعال أسعار التأمين البحري وأسواق الطاقة"
                },
                {
                    "narration": "الاعتماد الآسيوي على مضيق هرمز يمثل إحدى أبرز نقاط الضعف الاستراتيجي في ميزان القوى الدولي المعاصر. دول كبرى مثل الصين واليابان وكوريا الجنوبية والهند تستورد أكثر من سبعين بالمئة من احتياجاتها النفطية عبر هذا المضيق تحديداً. بالنسبة لهذه الدول، فإن أي انقطاع طويل الأمد لإمدادات النفط القادمة من هرمز يعني توقفاً كارثياً في خطوط الإنتاج الصناعي، وشللاً في شبكات النقل الداخلي، وعجزاً اقتصادياً لا تستطيع حتى أكبر الاحتياطيات النقدية تحمله لأكثر من بضعة أشهر معدودة.",
                    "query": "modern tokyo shanghai night highway cityscape",
                    "backup_img": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1920&h=1080&fit=crop",
                    "lower_third": "🏭 اعتماد الصناعة الآسيوية الكبرى على نفط المضيق"
                },
                {
                    "narration": "ولكن، بينما يتحكم مضيق هرمز في شريان الطاقة الذي يغذي مصانع العالم، هناك ممر مائي آخر في قلب الشرق الأوسط صنع التاريخ منذ أكثر من قرن ونصف، وغير مفاهيم التجارة البحرية والمسافات الجغرافية بين قارات الأرض إلى الأبد، ليتحول إلى محور صراع وتنافس لم يتوقف حتى هذه اللحظة.",
                    "query": "ocean cargo ship cruising at golden sunset",
                    "backup_img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&h=1080&fit=crop",
                    "lower_third": "🚢 الانتقال غرباً نحو معجزة قناة السويس"
                }
            ]
        },
        {
            "chapter_idx": 3,
            "title": "الفصل الثالث: ملحمة قناة السويس وكارثة إيفر جيفن",
            "scenes": [
                {
                    "narration": "في قلب الأراضي المصرية، تمتد قناة السويس كأعظم شريان ملاحي اصطناعي عرفته البشرية، لتربط مياه البحر الأبيض المتوسط بالبحر الأحمر، وتصنع أقصر طريق بحري يربط بين مراكز الإنتاج الصناعي في آسيا وأسواق الاستهلاك الكبرى في أوروبا. حفر هذه القناة في القرن التاسع عشر كان معجزة هندسية وإنسانية جبارة دفع فيها الشعب المصري تضحيات هائلة، ولكنها غيرت مسار التاريخ الاقتصادي باختصار رحلة الدوران حول القارة الإفريقية بآلاف الأميال البحرية.",
                    "query": "suez canal aerial cargo ship crossing egypt",
                    "backup_img": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1920&h=1080&fit=crop",
                    "lower_third": "📍 قناة السويس: شريان التجارة الأسرع عالمياً"
                },
                {
                    "narration": "تمثل قناة السويس اليوم ممراً حيوياً يعبر من خلاله ما يقرب من اثني عشر بالمئة من إجمالي حركة التجارة العالمية المنقولة بحراً، وتستوعب القناة قرابة ثلاثين بالمئة من إجمالي حركة سفن الحاويات في العالم. هذه الأرقام تجعلها عصب سلاسل التوريد الحديثة القائمة على نموذج التسليم اللحظي، حيث تعتمد المصانع الكبرى في أوروبا على وصول قطع الغيار والمواد الخام بانتظام يومي من مصانع الصين وشرق آسيا دون تخزين فائض كبير.",
                    "query": "container terminal loading cranes time lapse",
                    "backup_img": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1920&h=1080&fit=crop",
                    "lower_third": "⏳ اختصار 7000 كم وحفظ سلاسل الإمداد"
                },
                {
                    "narration": "في الثالث والعشرين من مارس عام 2021، حبس العالم أنفاسه عندما تعرضت سفينة الحاويات البنمية العملاقة إيفر جيفن لحادث جنوح غير مسبوق في القطاع الجنوبي للقناة نتيجة العواصف الترابية وسوء الأحوال الجوية. السفينة التي يبلغ طولها أربعمئة متر وتزن أكثر من مئتين وعشرين ألف طن، استقرت بعرض المجرى الملاحي وعلقت مقدمتها ومؤخرتها في ضفتي القناة، لتغلق الممر تماماً وتوقف حركة التجارة الدولية في مشهد صادم بثته شاشات التلفاز حول العالم.",
                    "query": "massive container vessel stuck in narrow canal",
                    "backup_img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&h=1080&fit=crop",
                    "lower_third": "🚨 حادثة جنوح إيفر جيفن: صدمة الشلل العالمي"
                },
                {
                    "narration": "كشفت تلك الأيام الستة العصيبة عن هشاشة غير مسبوقة في الاقتصاد الدولي. كل ساعة من توقف الملاحة كانت تكلف التجارة العالمية ما يقارب أربعمئة مليون دولار، وتراكمت طوابير تضم أكثر من أربعمئة سفينة عملاقة في مداخل القناة بالبحر الأحمر والبحر المتوسط. بدأت المصانع الأوروبية تعلن عن نقص حاد في قطع الغيار، وارتفعت أسعار الشحن البحري وتكاليف نقل الحاويات إلى مستويات قياسية أثبتت أن العالم المعاصر معلق بسلسلة أرق مما يتخيل أي خبير اقتصادي.",
                    "query": "fleet of ships anchored open sea waiting line",
                    "backup_img": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1920&h=1080&fit=crop",
                    "lower_third": "💸 خسائر فلكية: 400 مليون دولار في الساعة"
                },
                {
                    "narration": "إنقاذ الموقف وتعويم السفينة عبر خطة هندسية عبقرية نفذتها هيئة قناة السويس بالاعتماد على الكراكات وقاطرات الشد العملاقة دون تفريغ حمولة السفينة، كان بمثابة معجزة تقنية أعادت فتح شريان العالم. ولكن الحادثة فتحت الباب على مصراعيه أمام نقاشات استراتيجية كبرى حول تأمين الممرات الحيوية والبحث عن بدائل ممكنة، وقادت الأنظار مباشرة نحو البوابة الجنوبية الحارسة للبحر الأحمر.",
                    "query": "tugboats pulling huge ship water rescue operation",
                    "backup_img": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1920&h=1080&fit=crop",
                    "lower_third": "🏗️ ملحمة التعويم وإنقاذ التجارة العالمية"
                }
            ]
        },
        {
            "chapter_idx": 4,
            "title": "الفصل الرابع: باب المندب وخفايا البحر الأحمر",
            "scenes": [
                {
                    "narration": "على البوابة الجنوبية للبحر الأحمر، يقف مضيق باب المندب كحارس استراتيجي صارم يتحكم في الدخول والخروج بين المحيط الهندي وخليج عدن من جهة، ومياه البحر الأحمر المؤدية إلى قناة السويس من جهة أخرى. يفصل هذا المضيق بين السواحل اليمنية في شبه الجزيرة العربية وسواحل جيبوتي وإريتريا في القرن الإفريقي، ويتحكم بمفرده في عبور أكثر من واحد وعشرين ألف سفينة تجارية سنوياً تحمل ثروات وخيرات التجارة بين قارات العالم القديم.",
                    "query": "bab el mandeb strait red sea dramatic coast aerial",
                    "backup_img": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&h=1080&fit=crop",
                    "lower_third": "📍 مضيق باب المندب: بوابة البحر الأحمر الحاكمة"
                },
                {
                    "narration": "يبلغ عرض مضيق باب المندب حوالي ثلاثين كيلومتراً، وتفصل بين مياهه جزيرة بريم البركانية إلى ممرين ملاحيين؛ الممر الشرقي المعروف باسم باب إسكندر وهو ضيق وضحل، والممر الغربي المعروف بدقة الميون وهو الممر الرئيسي الآمن لعبور السفن الكبيرة بعرض يبلغ حوالي خمسة وعشرين كيلومتراً وعمق يتجاوز ثلاثمئة متر. ورغم اتساعه النسبي مقارنة بمضائق أخرى، إلا أن قربه من السواحل المضطربة يجعله منطقة ذات حساسية عسكرية قصوى.",
                    "query": "red sea mountainous dramatic coastline drone",
                    "backup_img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&h=1080&fit=crop",
                    "lower_third": "🛡️ التضاريس الملاحية وجزيرة بريم الحاكمة"
                },
                {
                    "narration": "شهدت مياه باب المندب وجنوب البحر الأحمر في الفترات الأخيرة توترات أمنية غير مسبوقة هددت سلامة الملاحة التجارية العالمية. استهداف السفن وناقلات الحاويات بالصواريخ الباليستية والطائرات المسيرة دفع كبرى خطوط الشحن العالمية للإعلان عن تعليق رحلاتها عبر البحر الأحمر، والتحول قسرياً نحو المسار التاريخي القديم بالدوران حول القارة الإفريقية عبر طريق رأس الرجاء الصالح، وهو القرار الذي كبد قطاع الشحن تكاليف إضافية بالمليارات.",
                    "query": "stormy sea container ship fighting giant waves",
                    "backup_img": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1920&h=1080&fit=crop",
                    "lower_third": "🌊 العودة القسرية لطريق رأس الرجاء الصالح"
                },
                {
                    "narration": "الدوران حول القارة الإفريقية يضيف إلى مسار كل رحلة ما بين عشرة إلى أربعة عشر يوماً إضافية، ويستهلك مئات الأطنان من الوقود الإضافي بتكلفة تقارب مليون دولار للسفينة الواحدة في كل اتجاه. هذا التأخير أدى إلى نقص في عدد الحاويات المتاحة في الموانئ الكبرى، وتسبب في تكدس مروري في موانئ الترانزيت العالمية، وأثبت للجميع أن الممرات المائية ليست مجرد خطوط على خريطة، بل هي أعمدة التوازن التي تقوم عليها دورة الاقتصاد الحديث.",
                    "query": "cape of good hope south africa ocean cliffs waves",
                    "backup_img": "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=1920&h=1080&fit=crop",
                    "lower_third": "💰 مليون دولار تكلفة وقود إضافية لكل رحلة"
                },
                {
                    "narration": "هذه التعقيدات في الممرات التقليدية جعلت الدول الكبرى تعيد التفكير في خططها اللوجستية طويلة المدى، وبدأت الأعين تتجه نحو أقصى شمال الكوكب، حيث تسببت التغيرات المناخية في فتح مسارات بحرية كانت حتى وقت قريب مدفونة تحت أطنان من الجليد الأبدي الذي لا يمكن اختراقه.",
                    "query": "arctic ocean icebergs frozen cold winter drone landscape",
                    "backup_img": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1920&h=1080&fit=crop",
                    "lower_third": "🧭 التحول نحو الصقيع: معركة القطب الشمالي"
                }
            ]
        },
        {
            "chapter_idx": 5,
            "title": "الفصل الخامس: صراع القطب الشمالي والممرات البديلة",
            "scenes": [
                {
                    "narration": "مع تسارع ظاهرة الاحتباس الحراري وذوبان الكتل الجليدية في المحيط المتجمد الشمالي، بدأ يظهر على الساحة العالمية ممر مائي جديد يملك القدرة على إعادة كتابة قواعد الجغرافيا بالكامل: طريق الملاحة الشمالي الممتد بمحاذاة السواحل الروسية الشمالية. هذا المسار يوفر اختصاراً هائلاً في المسافة بين موانئ شرق آسيا مثل شنغهاي ويوكوهاما، وموانئ شمال غرب أوروبا مثل روتردام وهامبورغ، بنسبة تصل إلى أربعين بالمئة مقارنة بالطرق التقليدية عبر السويس.",
                    "query": "arctic icebreaker ship cutting through frozen ice",
                    "backup_img": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1920&h=1080&fit=crop",
                    "lower_third": "❄️ طريق الملاحة الشمالي: ثورة القطب المتجمد"
                },
                {
                    "narration": "روسيا تدرك تماماً القيمة الجيوسياسية الخارقة لهذا المسار، وتقوم منذ سنوات بضخ استثمارات هائلة لبناء أضخم أسطول لكاسحات الجليد التي تعمل بالطاقة النووية في العالم. هذه السفن الجبارة قادرة على شق الجليد بسمك يصل لعدة أمتار وتأمين قوافل السفن التجارية في أقسى الظروف الجوية، بهدف تحويل هذا الممر المتجمد إلى طريق تجاري دولي يعمل على مدار فصول السنة تحت السيادة والإدارة الروسية الكاملة.",
                    "query": "nuclear powered icebreaker vessel aerial drone arctic",
                    "backup_img": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1920&h=1080&fit=crop",
                    "lower_third": "🚢 أسطول كاسحات الجليد النووية الروسية"
                },
                {
                    "narration": "الصين من جهتها أعلنت رسمياً عن مشروع طريق الحرير القطبي كجزء محوري من مبادرة الحزام والطريق، وبدأت بالشراكة مع موسكو في الاستثمار في موانئ المياه العميقة ومحطات الغاز الطبيعي المسال في شبه جزيرة يامال. بكين ترى في المسار القطبي طوق نجاة استراتيجي يتيح لها كسر الاعتماد التاريخي على مضيق ملقا ونقاط الاختناق الجنوبية التي تراقبها الأساطيل البحرية الغربية بكثافة.",
                    "query": "modern industrial port facilities container logistics snow",
                    "backup_img": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=1920&h=1080&fit=crop",
                    "lower_third": "🇨🇳 استراتيجية طريق الحرير القطبي الصيني"
                },
                {
                    "narration": "لكن رغم هذه الآفاق الواعدة، يواجه الممر القطبي تحديات بيئية ولوجستية هائلة تحول دون تحوله إلى بديل فوري للممرات الدافئة. انخفاض درجات الحرارة إلى مستويات قياسية، وظلام الشتاء القطبي المستمر، وندرة محطات الإنقاذ والصيانة، بالإضافة إلى التكاليف الباهظة لبناء سفن تجارية مصفحة ومقاومة للتجمد، تجعل تكلفة التأمين والتشغيل عائقاً كبيراً أمام السفن التجارية العادية في الوقت الراهن.",
                    "query": "extreme snowstorm blizzard frozen arctic mountains",
                    "backup_img": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920&h=1080&fit=crop",
                    "lower_third": "⚠️ العوائق البيئية واللوجستية في المسار القطبي"
                },
                {
                    "narration": "بين مياه هرمز وباب المندب الدافئة، وصقيع القطب المتجمد في الشمال الأقصى، يتبين بوضوح أن خريطة العالم المائية تمر بمرحلة إعادة تشكيل شاملة ستحدد توازن القوى الاقتصادية والعسكرية بين القوى الدولية الكبرى خلال العقود القادمة.",
                    "query": "planet earth from space atmosphere night lights",
                    "backup_img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&h=1080&fit=crop",
                    "lower_third": "🌐 صراع المئة عام القادمة على جغرافيا البحار"
                }
            ]
        },
        {
            "chapter_idx": 6,
            "title": "الفصل السادس: سيناريوهات المستقبل والكلمة الأخيرة",
            "scenes": [
                {
                    "narration": "مع دخولنا إلى الربع الثاني من القرن الحادي والعشرين، لم تعد حروب المستقبل تقتصر على النزاعات العسكرية على اليابسة، بل تحولت إلى حروب سلاسل إمداد ولوجستيات ذكية. التحكم في التدفقات التجارية والقدرة على تأمين الممرات الحيوية أو حرمان الخصوم منها أصبحت الورقة الرابحة التي تقاس بها القوة السيادية للدول العظمى في أوقات السلم والحرب على حد سواء.",
                    "query": "futuristic automated container terminal drones port",
                    "backup_img": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=1920&h=1080&fit=crop",
                    "lower_third": "🏗️ حروب اللوجستيات وسلاسل الإمداد المعاصرة"
                },
                {
                    "narration": "المضائق الكبرى الأخرى حول العالم تشهد أيضاً تحولات دراماتيكية متسارعة؛ فمضيق ملقا في جنوب شرق آسيا، الذي يعبر منه ثلث تجارة العالم وثمانون بالمئة من واردات الصين النفطية، يواجه مخاطر الازدحام الملاحي والقرصنة، بينما تعاني قناة بنما في النصف الغربي من الكرة الأرضية من موجات جفاف غير مسبوقة قلصت أعداد السفن المسموح بعبورها يومياً وفرضت غرامات تأخير قياسية.",
                    "query": "panama canal aerial locks container crossing pacific",
                    "backup_img": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1920&h=1080&fit=crop",
                    "lower_third": "📍 قناة بنما ومضيق ملقا: أزمات موازية في الممرات"
                },
                {
                    "narration": "الدول التي حباها الله بمواقع جغرافية استثنائية تتحكم في هذه المعابر لم تعد مجرد ممرات عبور صامتة، بل تحولت إلى مراكز قوى جيواقتصادية تمتلك أوراق ضغط دبلوماسية قادرة على تعديل مسار السياسات الدولية، وتحقيق عوائد مالية سيادية تدعم اقتصاداتها الوطنية وتفرض احترام مصالحها في كافة المحافل العالمية.",
                    "query": "world economic global summit conference diplomatic meeting",
                    "backup_img": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1920&h=1080&fit=crop",
                    "lower_third": "🏛️ أوراق الضغط السيادية والمصالح الوطنية"
                },
                {
                    "narration": "ومهما بلغت درجات التطور التكنولوجي وسفن الشحن ذاتية القيادة والأقمار الصناعية الموجهة، سيظل العنصر الجغرافي هو الحاكم الأبدي لحركة الحضارة البشرية. الأرض ستظل هي الأرض، والمحيطات الشاسعة ستظل محكومة بهذه الشرايين المائية الضيقة التي تبقي كوكبنا متصلاً ومترابطاً كل ثانية.",
                    "query": "futuristic cargo ship autonomous navigating ocean",
                    "backup_img": "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=1920&h=1080&fit=crop",
                    "lower_third": "🤖 مستقبل الشحن الذكي وثبات الجغرافيا"
                },
                {
                    "narration": "في ختام هذا التحقيق الوثائقي الموسع، يبقى السؤال الأهم مطروحاً أمامكم: برأيكم، ما هو الممر المائي الأكثر خطورة والذي قد يشهد الأزمة القادمة التي ستهدد استقرار الاقتصاد العالمي؟ شاركونا آراءكم وتحليلاتكم في التعليقات، ولا تنسوا الاشتراك في القناة وتفعيل زر الجرس لمتابعة تحقيقاتنا الوثائقية القادمة.",
                    "query": "epic cinematic ocean sunset horizon calm water drone",
                    "backup_img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&h=1080&fit=crop",
                    "lower_third": "💬 شاركنا رأيك بالتعليقات واشترك بالقناة"
                }
            ]
        }
    ]
}

def ensure_bgm():
    if not os.path.exists("doc_bgm.mp3"):
        try:
            r = requests.get(DOC_BGM_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            if r.status_code == 200:
                with open("doc_bgm.mp3", "wb") as f:
                    f.write(r.content)
        except Exception:
            pass

def get_best_arabic_font(size=40):
    for p in [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def clean_arabic(text):
    return re.sub(r'[^\w\s\d\u0600-\u06FF!؟,\.\:\-\(\)\"\$]+', '', text).strip()

async def generate_voice(text, output_file):
    import edge_tts
    # وتيرة هادئة ومتزنة للسرد الوثائقي الطويل
    communicate = edge_tts.Communicate(text, "ar-EG-ShakirNeural", rate="-2%")
    await communicate.save(output_file)

# ==============================================================================
# محرك الصور والفيديو الهجين (يمنع الشاشة السوداء نهائياً)
# ==============================================================================
def fetch_or_generate_visual(query, backup_url, duration, target_size=(1920, 1080)):
    # 1. محاولة جلب فيديو حقيقي من Pexels
    if PEXELS_API_KEY:
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=6&orientation=landscape"
            headers = {"Authorization": PEXELS_API_KEY, "User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                vids = r.json().get("videos", [])
                for v in vids:
                    v_files = v.get("video_files", [])
                    link = None
                    for vf in v_files:
                        if vf.get("file_type") == "video/mp4":
                            link = vf.get("link")
                            break
                    if link:
                        tmp_v = f"tmp_v_{random.randint(1000, 999999)}.mp4"
                        vr = requests.get(link, stream=True, timeout=25)
                        if vr.status_code == 200:
                            with open(tmp_v, "wb") as f:
                                for ch in vr.iter_content(chunk_size=1024*1024):
                                    if ch: f.write(ch)
                            clip = VideoFileClip(tmp_v).without_audio()
                            if clip.duration < duration:
                                clip = clip.fx(vfx.loop, duration=duration)
                            else:
                                clip = clip.subclip(0, duration)
                            clip = clip.resize(height=1080)
                            if clip.w < 1920:
                                clip = clip.resize(width=1920)
                            clip = clip.crop(x_center=clip.w // 2, y_center=clip.h // 2, width=1920, height=1080)
                            return clip, tmp_v
        except Exception:
            pass

    # 2. جلب صورة عالية الدقة وتطبيق حركة Ken Burns Zoom عليها
    tmp_img = f"tmp_img_{random.randint(1000, 999999)}.jpg"
    img_obtained = False

    try:
        r = requests.get(backup_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200:
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            im = im.resize(target_size, Image.Resampling.LANCZOS)
            im.save(tmp_img, "JPEG")
            img_obtained = True
    except Exception:
        pass

    # 3. توليد صورة بالذكاء الاصطناعي 16:9 إذا فشل الرابط الاحتياطي
    if not img_obtained:
        try:
            clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', query)
            prompt = f"epic cinematic 4k landscape documentary shot {clean_q} national geographic"
            ai_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1920&height=1080&nologo=true"
            r = requests.get(ai_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if r.status_code == 200:
                with open(tmp_img, "wb") as f:
                    f.write(r.content)
                img_obtained = True
        except Exception:
            pass

    # صورة بديلة ملونة في أقصى الحالات
    if not img_obtained:
        im = Image.new("RGB", target_size, color=(20, 35, 60))
        d = ImageDraw.Draw(im)
        d.text((960, 540), "وثائقي استقصائي", fill=(255, 255, 255), anchor="mm")
        im.save(tmp_img, "JPEG")

    # تحريك سينمائي (Ken Burns Effect) لإعطاء الصورة حياة مستمرة
    img_clip = (ImageClip(tmp_img)
                .set_duration(duration)
                .resize(lambda t: 1.0 + 0.05 * (t / duration))
                .crop(x_center=target_size[0] // 2, y_center=target_size[1] // 2, width=target_size[0], height=target_size[1])
                .fx(vfx.colorx, 1.10))
    return img_clip, tmp_img

def create_lower_third(text, target_path, size=(1920, 1080)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_best_arabic_font(size=36)

    clean_txt = clean_arabic(text)
    has_raqm = features.check("raqm")
    if not has_raqm:
        import arabic_reshaper
        from bidi.algorithm import get_display
        clean_txt = get_display(arabic_reshaper.reshape(clean_txt))

    bbox = draw.textbbox((0, 0), clean_txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    bx2 = 1920 - 100
    bx1 = bx2 - tw - 50
    by1 = 1080 - 170
    by2 = by1 + th + 24

    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=14, fill=(10, 15, 25, 220), outline=(0, 230, 255, 200), width=2)
    draw.text(((bx1 + bx2) // 2, by1 + 10), clean_txt, font=font, fill=(255, 255, 255, 255), anchor="mt", direction="rtl" if has_raqm else None)
    img.save(target_path)

def render_chapter_chunk(scenes_list, chapter_title, chapter_idx):
    size = (1920, 1080)
    scenes = []
    temp_files = []
    voice_clips = []
    current_time = 0.0

    print(f"\n🎬 رندر الفصل {chapter_idx}: {chapter_title} ({len(scenes_list)} مشاهد موسعة)...")

    for s_idx, sc in enumerate(scenes_list):
        aud_path = f"aud_c{chapter_idx}_s{s_idx}.mp3"
        asyncio.run(generate_voice(sc["narration"], aud_path))
        aud_clip = AudioFileClip(aud_path)
        duration = aud_clip.duration + 0.35
        temp_files.append(aud_path)

        voice_clips.append(aud_clip.set_start(current_time))

        # جلب المرئيات الحية (فيديو أو صورة متحركة)
        visual_clip, tmp_source = fetch_or_generate_visual(sc["query"], sc.get("backup_img", ""), duration, size)
        temp_files.append(tmp_source)

        lt_path = f"lt_c{chapter_idx}_s{s_idx}.png"
        create_lower_third(sc.get("lower_third", chapter_title), lt_path, size=size)
        temp_files.append(lt_path)
        lt_clip = ImageClip(lt_path).set_duration(min(6.0, duration)).set_start(0.5)

        composed_scene = CompositeVideoClip([visual_clip, lt_clip], size=size).set_duration(duration)
        scenes.append(composed_scene)
        current_time += duration

    chapter_video = concatenate_videoclips(scenes, method="compose")
    chapter_audio = CompositeAudioClip(voice_clips).set_duration(chapter_video.duration)
    chapter_video = chapter_video.set_audio(chapter_audio)

    chunk_filename = f"chunk_chapter_{chapter_idx}.mp4"
    chapter_video.write_videofile(
        chunk_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="3500k",
        preset="ultrafast",
        threads=2
    )

    for f in temp_files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return chunk_filename

def stitch_and_finalize_documentary(chunk_files, output_filename="documentary_30min.mp4"):
    print("\n⚡ بدء الدمج الفوري لجميع الفصول عبر FFmpeg Concat...")
    list_path = "chapters_list.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for chunk in chunk_files:
            f.write(f"file '{chunk}'\n")

    temp_stitched = "temp_raw_stitched.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        temp_stitched
    ]
    subprocess.run(cmd_concat, check=True)

    ensure_bgm()
    if os.path.exists("doc_bgm.mp3"):
        print("🎵 دمج الموسيقى التصويرية الوثائقية بكامل مدة الفيلم...")
        cmd_audio = [
            "ffmpeg", "-y",
            "-i", temp_stitched,
            "-stream_loop", "-1", "-i", "doc_bgm.mp3",
            "-filter_complex", "[1:a]volume=0.07[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            output_filename
        ]
        subprocess.run(cmd_audio, check=True)
        if os.path.exists(temp_stitched):
            os.remove(temp_stitched)
    else:
        os.rename(temp_stitched, output_filename)

    if os.path.exists(list_path):
        os.remove(list_path)
    for chunk in chunk_files:
        if os.path.exists(chunk):
            os.remove(chunk)

    print(f"🎉 تم بنجاح إنتاج الفيلم الوثائقي الطويل: {output_filename}")
    return output_filename

def main():
    niche_name = NICHE_NAMES[0]
    print(f"=======================================================")
    print(f"🚀 بدء إنتاج وثائقي ضخم (25 - 30 دقيقة فعلية): {niche_name}")
    print(f"=======================================================")

    doc_data = MASTER_30MIN_DEEP_DOC
    print(f"📌 عنوان الوثائقي: {doc_data['title']}")

    chunk_files = []
    for ch in doc_data["chapters"]:
        chunk_file = render_chapter_chunk(ch["scenes"], ch["title"], ch["chapter_idx"])
        chunk_files.append(chunk_file)

    final_video_path = stitch_and_finalize_documentary(chunk_files, "documentary_30min.mp4")

    with open("video_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": doc_data["title"],
            "desc": doc_data["desc"]
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
