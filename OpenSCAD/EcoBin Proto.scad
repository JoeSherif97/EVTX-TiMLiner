// =========================================================================
// مشروع الصندوق الهندسي - إصدار متكامل ومعدل الأبعاد بالكامل
// نقطة الأصل (0,0,0) هي الكورنر (تحت - شمال - وراء)
// جميع الأبعاد بالمليمتر (mm)
// =========================================================================

$fn = 80; // تنعيم عالي للأجزاء الدائرية

// --- الأبعاد الهيكلية الأساسية الجديدة (تعديل الأبعاد حسب طلبك) ---
box_w = 440;  // العرض: أكتر من 40 وأقل من 46 سنتي (اخترنا 440 مم)
box_l = 270;  // الطول: أكتر من 25 وأقل من 27 سنتي (اخترنا 270 مم لاستيعاب اللوح تماماً)
box_h = 260;  // الارتفاع: أكتر من 24 وأقل من 28 سنتي (اخترنا 260 مم)
wall_t = 5;   

// بيت الدائرة (نفس الأبعاد بدون تصغير)
circuit_w = 110;
circuit_h = 70;
circuit_d = 50;

// فتحة الموتور (نفس الأبعاد بدون تصغير)
servo_w = 42.5;
servo_h = 20;

// اللوح الداخلي (نفس الأبعاد بدون تصغير)
plate_w = 400;
plate_l = 250;
plate_t = 6; 

// الفاصل السفلي (تم تعديل العرض ليصبح نصف سنتي = 5 مم)
separator_w = 5; 
separator_h = box_h - 107; // تعديل تلقائي للارتفاع ليحافظ على مكانه الصحيح أسفل الموتور

// أبعاد جيب مروحة السيرفو
pocket_w = 50;
pocket_h = 30;
pocket_d = 10;

// --- [أبعاد الخطافات المعتمدة من طرفك] ---
hook_w = 25;  
hook_l = 5;   
hook_h = 12;  

// --- الأكواد اللونية لمحاكاة الخشب ---
wood_light = [0.85, 0.70, 0.50];  
wood_dark  = [0.60, 0.40, 0.20];  
wood_frame = [0.73, 0.56, 0.36];  

// --- استدعاء التجميعة الكاملة ---
main_assembly();

module main_assembly() {
    
    // 1. الهيكل الخارجي للصندوق الخشبي مع المقابض والفتحات
    color(wood_frame) {
        difference() {
            cube([box_w, box_l, box_h]);
            
            // التجويف الداخلي للصندوق
            translate([wall_t, wall_t, wall_t])
                cube([box_w - 2*wall_t, box_l - 2*wall_t, box_h]);
            
            // فتحة الموتور الدقيقة موسطة تماماً على الواجهة الأمامية
            translate([(box_w/2) - (servo_w/2), box_l - wall_t - 1, box_h - 67]) 
                cube([servo_w, wall_t + 2, servo_h]);
                
            // مقبض الحمل الأيمن
            translate([box_w - wall_t - 1, box_l/2 - 50, box_h - 80])
                handle_slot();
                
            // مقبض الحمل الأيسر
            translate([-1, box_l/2 - 50, box_h - 80])
                handle_slot();
        }
    }
    
    // 2. بيت الدائرة الخارجي (Circuit House) - موسط ومفتوح يساراً وبفتحة سلك يميناً
    color(wood_light) {
        translate([(box_w/2) - (circuit_w/2), box_l, box_h - 140]) {
            difference() {
                cube([circuit_w, circuit_d, circuit_h]);
                
                // فتحة الجانب الأيسر لدخول الدائرة سليدنج
                translate([-1, -1, wall_t])
                    cube([circuit_w - wall_t + 1, circuit_d - wall_t + 1, circuit_h - 2*wall_t]);
                
                // فتحة السلك المربعة (15x15 مم) على اليمين
                translate([circuit_w - wall_t - 1, (circuit_d - 15)/2, (circuit_h - 15)/2])
                    cube([wall_t + 2, 15, 15]);
            }
        }
    }
    
    // 3. الفاصل السفلي الثابت (موسط تماماً وبعرض 5 مم)
    color(wood_dark) {
        translate([(box_w/2) - (separator_w/2), wall_t, wall_t])
            cube([separator_w, box_l - 2*wall_t, separator_h]);
    }
    
    // 4. اللوح الداخلي المتحرك - متناسق وموسط تماماً مع الأبعاد الجديدة
    translate([box_w/2, box_l - 15, box_h - 57]) 
        rotate([0, 0, 0]) // زاوية الدوران التجريبية للموتور
            tilting_plate_assembly();
}

// موديول مقبض اليد
module handle_slot() {
    hull() {
        translate([0, 20, 0]) cylinder(h=40, r=15, center=false);
        translate([0, 80, 0]) cylinder(h=40, r=15, center=false);
    }
}

// موديول مخصص لبناء الخطاف الواحد بالأبعاد المطلوبة وتفريغه داخلياً
module single_hook() {
    difference() {
        cube([hook_w, hook_l, hook_h]);
        
        // التجويف الداخلي للخطاف ليصبح كالحاضن أو المجرى
        translate([1.5, -1, 3])
            cube([hook_w - 1.5 + 1, hook_l + 2, hook_h - 3 + 1]);
    }
}

// موديول اللوح الداخلي المتكامل مع شفة الجيب والخطافات السفلية
module tilting_plate_assembly() {
    // أ) اللوح الأفقي الأساسي
    color(wood_light) {
        translate([-plate_w/2, -plate_l, -plate_t/2])
            cube([plate_w, plate_l, plate_t]);
    }
    
    // ب) جيب مروحة السيرفو (الشفة البارزة بين اللوح والفتحة)
    color(wood_dark) {
        translate([-pocket_w/2, 0, -pocket_h/2]) {
            difference() {
                cube([pocket_w, pocket_d, pocket_h]);
                translate([(pocket_w - 40)/2, -1, (pocket_h - 24)/2])
                    cube([40, 8, 24]);
                translate([pocket_w/2, pocket_d + 1, pocket_h/2])
                    rotate([90, 0, 0])
                        cylinder(h = pocket_d + 2, r = 3);
            }
        }
    }
    
    // ج) الخطاف الأيسر (بين الربع 1 و 2 في منتصف الطول تماماً، لازق تحت اللوح)
    translate([-plate_w/4 - hook_w/2, -plate_l/2 - hook_l/2, -plate_t/2 - hook_h])
        color(wood_dark) 
            single_hook();

    // د) الخطاف الأيمن (بين الربع 3 و 4 في منتصف الطول تماماً، لازق تحت اللوح)
    translate([plate_w/4 + hook_w/2, -plate_l/2 - hook_l/2, -plate_t/2 - hook_h])
        mirror([1, 0, 0])
            color(wood_dark) 
                single_hook();
}