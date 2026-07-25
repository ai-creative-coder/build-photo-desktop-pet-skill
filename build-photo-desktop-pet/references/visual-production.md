# Visual production workflow

## Contents

1. Source photo and subject bible
2. Clean base and chibi proportions
3. Chibi base and turnaround
4. State stills and transparency
5. Key poses and 12-frame motion
6. Anchors, masks and effects
7. Known failure modes

## 1. Source photo and subject bible

Inspect every supplied image before generation. Identify the intended person or animal only from visible evidence. Ask which subject to use only when multiple plausible subjects exist. Do not infer sensitive identity attributes or an uncertain animal breed.

Record applicable invariants in `character-spec.md`:

- person: hair, face, wardrobe, shoes and visible accessories;
- animal: body shape, coat/feather/scale pattern, ears, muzzle/beak, paws/hooves/wings, tail and collar/harness;
- face/eye features and stable color markings;
- original pose, occluded body regions and any necessary reconstruction;
- keep list, removal list and minimal-inference list;
- chibi head-to-body ratio and line/shading style;
- features that may never be added, removed or redesigned.

Use only the current user's photo as the identity/appearance reference, not as a one-click cartoon filter. Preserve recognizable visible features without photorealistic cloning. Never use a prior user's source or derived character as an example or fallback.

If a separate proportion reference is supplied, use it only for geometry. Never copy its face, clothing, pose, accessories, rendering identity or private subject details.

## 2. Clean base and chibi proportions

Treat the base as an animation-ready neutral master, not a literal copy of the photo pose.

For a person, remove by default:

- handheld and carried objects, including the object body, handles, straps and packaging;
- chairs, tables, sports gear, scenery, decorative effects, floor shadows and reflections;
- text, numbers, logos, watermarks, color cards and AI marks.

Distinguish worn identity accessories from held props. Keep a hat worn on the head, earrings, necklace, watch or bracelet when identity-relevant. Remove a hat held in a hand and remove an unwanted shoulder bag together with every strap. List each visible removal explicitly in the generation prompt. After removal, require two complete empty hands in a relaxed pose; reject gripping air, missing fingers and a residual object-holding pose. For animals, remove leashes, toys, bowls and scene props unless the collar or harness is part of the approved identity; preserve species-appropriate paws, wings, hooves or fins instead of inventing human hands.

Use minimal necessary inference for occluded shoes, legs, skirt hems, paws or tails. Continue confirmed palette, season and clothing/morphology. Choose low-complexity, animation-friendly reconstruction and record every inferred feature. Ask before proceeding when the missing region would materially change identity.

For an upright human or explicitly anthropomorphic character, default to `2.6–2.7` heads from the highest hair/hat point to the sole baseline; the head occupies roughly `37–39%` of total height. Keep head width slightly greater than shoulder width, compact torso and limbs, readable hands and feet, and enough body length for typing, walking and gesture animation. Do not default to extreme `2.0–2.2` heads or ordinary `3+` head anime proportion. For a natural quadruped, bird, fish or other non-human animal, preserve recognizable species geometry and choose a similarly readable enlarged-head chibi balance instead of forcing a human head-count formula.

Do not approve proportions by eye or prompt wording alone. On the selected base, record `top_y` at the highest hair/hat point, `chin_y` at the chin and `baseline_y` at the shared sole line. Compute `total_height = baseline_y - top_y`, `head_height = chin_y - top_y`, `heads_tall = total_height / head_height` and `head_fraction = head_height / total_height`. Run `scripts/validate_character_proportions.py` and keep its JSON plus overlay. Reject an upright base below `2.6`, above `2.7`, below `37%` head fraction or above `39%` unless the user explicitly approved another ratio.

When revising head size, lock the body scale and sole/contact baseline. State the head-only percentage change, scale face and hair together, and forbid whole-subject rescaling. Reject any revision that changes body pixel scale, contact coordinates or canvas padding.

Keep prior versions instead of overwriting them. Name the chroma and RGBA pair with the same version suffix, and record the input, removal list, inference list, prompt, ratio, alpha checks and approval/rejection reason in `character/generation-log.md`.

Use a neutral front or slight three-quarter standing/contact pose, centered weight, compact foot spacing and empty visible extremities. Leave safety padding around hair/ears, elbows/wings, clothing/tail and soles/paws. Use the center of the sole/contact region and its lowest stable line as the future animation anchor, not the full alpha bounding box.

## 3. Chibi base and turnaround

Generate one full-body base subject first. Require generous padding around the full silhouette, extremities, ears/hair, tail and contact points, with enough clarity at roughly 300 px height. Inspect the output before deriving variants.

Then generate a turnaround board containing front, side, back, front three-quarter and back three-quarter views plus face/outfit details. Check:

- constant head-to-body ratio and head width;
- same hair/fur/feather structure, ears and tail;
- spatially consistent clothing, coat markings, collar/harness and contact anatomy;
- no front-only structure on the back view;
- same camera height, palette, line weight and rendering family.

The turnaround is structural reference, not animation frames.

Use the approved neutral standing RGBA base itself as the project/program icon source. Do not ask ImageGen to redraw a separate icon, because that can change identity or proportions. Fit the complete standing silhouette uniformly onto the standard icon background with generous head/hair/ear, elbow/wing, clothing/tail and sole/paw padding. Do not use a seated, coding, drinking or reminder state; do not include furniture, props, effects, text, watermark or speech bubble. Review the composed icon at 256, 128, 64 and 32 px. The reusable Skill contains one explicitly authorized generic standing chibi only in its three application-icon files. Treat it solely as a structural placeholder, never as an identity, clothing, proportion or style reference. User-derived PNG/ICO/ICNS files belong only to that user's generated project and installer and must replace the placeholder before packaging.

## 4. State stills and transparency

Generate every state separately from the approved base. Do not ask one image call to create all states. For each state, inspect anatomy, clothing, props and real-world spatial logic before animation. A coding scene must put content on the monitor front, keep both hands over the keyboard and place the character where they can see the screen. Prefer an over-the-shoulder or rear three-quarter camera: the character may face away from the user while the monitor front remains visible at an oblique angle, so alternating typing hands and changing screen data are readable together. Reject any view that shows changing data on the monitor back.

The base-master cleanup rule does not ban functional state props. Add a keyboard, monitor, chair, cup, magnifier or clock only when required by that state, and remove it again from states that do not need it.

Use Codex built-in `image_gen` first. If it is unavailable or this Skill is running outside Codex, do not generate until the user configures and approves an external provider through `image-provider-configuration.md`. For transparency, request a perfectly flat chroma-key field, normally `#00ff00`, with no shadow, floor, gradient, reflection or texture. If the subject contains substantial bright green, use a non-conflicting flat magenta key instead. Do not use the chosen key color in the subject. Save both the selected chroma-key PNG and the converted RGBA PNG in the user's private project. Run the installed imagegen `remove_chroma_key.py` helper with soft matte and despill.

Ban floor planes, cast shadows, contact shadows and reflections from every state, including beneath chairs, desks and feet/paws. Reject them in the generated pixels instead of hiding them with runtime cropping. The app must not add CSS `drop-shadow` filters or synthetic ground-shadow pseudo-elements beneath the character.

Inspect alpha on checkerboard, white and dark backgrounds. Pay special attention to:

- individual hair/fur/feather tips and fingers/paws;
- laces, boot soles, claws/hooves and thin linework;
- holes between legs, arms, chair parts and table legs;
- monitor, keyboard, cup, clock and magnifier outlines;
- green fringe and magenta/purple reverse-despill fringe.

Transparent corners are only a minimum check. Inspect all pixels with `0 < alpha < 255`. Preserve fine structures; never use uniform erosion as a general fringe fix.

## 5. Key poses and 12-frame motion

Default to 12 frames at `384x341`. Use 140 ms per frame for short interactions and 180–220 ms for slow idle or stretch motion. Use 24 frames only when additional unique poses materially improve a large, slow action; duplicated or interpolated frames do not add real motion quality.

Before rendering frames, write a semantic motion plan. Each loop must change at least two of: expression/eyelids/mouth, gaze/head intent, limb joints/fingers, held-object pose, object contents/progress or detached effect. An idle loop may use blink, eye focus, mouth and a small hair-tip settle; it must not simulate life by moving or scaling the entire subject.

Use this rhythm:

- frame 1: start pose compatible with idle;
- frames 2–3: anticipation;
- frames 4–9: main action and peak;
- frames 10–11: settle;
- frame 12: return close to frame 1.

For drag/cheer, make the intention immediately readable: effort/cheer during movement, then a positive smile, wink, fist/thumbs-up or celebratory effect. Do not use a neutral standing loop, random wobble or unrelated action as drag feedback.

Treat a 4x3 ImageGen storyboard as an action draft only. Independent cells usually redraw the body, furniture and camera. Choose one correct reference scene. Reuse static pixels. Generate only 2–5 clean key poses for complex movement, preferably by editing the same approved base so all poses share a generation lineage.

Use local layer animation for changes wholly inside a stable outline: eye highlights, screen data, cup bubbles and detached effects. Use full-body or full-scene key poses whenever a change crosses a face outline, hair/fur, limb root, wrist/paw, sleeve, torso joint, tail or held prop.

Do not use mesh warping on fingers, keyboards, magnifiers, clocks or other objects with strong structural lines. It creates water-ripple motion.

Do not use `Image.blend` or opacity cross-fades between two complete redrawn key poses. Both bodies, faces, limbs, furniture and props become visible simultaneously and read as severe ghosting. Normalize each clean key pose once to a shared visual height/contact baseline, then use intentional holds and direct pose changes. Preserve all 12 timing frames in the APNG container instead of inventing pixel noise to prevent encoder frame merging.

## 6. Anchors, masks and effects

Never align by the full alpha bounding box. Raised limbs, hair/fur, ears, tails and effects change that box and push the body in the opposite direction.

Use:

- horizontal anchor: center of the lower foot/scene region;
- vertical anchor: lowest stable foot/paw/hoof/table baseline;
- one uniform scale for the entire animation (`scaleX = scaleY`);
- subject-scale landmark: a stable head/hat/shoulder width or head-top-to-contact distance that excludes detached effects, raised extremities and changing props;
- secondary checks: body/pelvis center, limb-root line and head center.

Recommended character-only baseline is `x=192`, `y=332`. Require zero-pixel vertical baseline drift for non-locomotion desktop-pet loops. A one-pixel tolerance is reserved only for a documented locomotion/contact change and still requires visual approval. Do not rescale individual frames. If a pose remains a different size under the shared transform, regenerate it.

Measure the chosen subject-scale landmark from the decoded clean key poses, not only from generation metadata. Allow at most a 1 px range for a height landmark or 2 px for a width landmark. When the action covers or changes the first landmark, choose another stable landmark. Never use changing furniture, screen content, effects, raised hands or the full alpha rectangle to determine character scale.

Extract stars, question marks, alert lines, bells and clock glows with connected components or exact alpha masks. A rectangular crop may not contain hair/fur, fingers/paws, wings or clothing. Produce a subject-protection/effect/overlap audit image; effect/subject overlap must be zero unless the effect is deliberately attached.

When motion involves posture, preserve the full kinetic chain from head and limb roots through torso/body center to contact limbs and tail. Do not freeze one body half and paste a changed half across a major joint.

## 7. Known failure modes

| Symptom | Cause | Required response |
|---|---|---|
| Character shifts sideways | Full bounds used as center | Align by lower stable anchor |
| Character breathes in size | Per-frame fit or non-uniform scale | One shared uniform transform |
| Stable canvas but internal shaking | Each frame was redrawn | One base plus layers/full key poses |
| Character only floats or bobs | Whole-subject translation/scale used as motion | Freeze root/baseline and animate expression, joints and props |
| Twelve frames differ by a pixel | Encoder-uniqueness hack | Remove fake glint/noise and add legitimate semantic transition frames |
| Jump at frames 5 or 9 | Storyboard row-scale clusters | Reject direct storyboard playback |
| Black block or extremity fragment | Mechanical grid split | Connected-component ownership audit |
| Hair/fur/finger/paw moves with icon | Rectangular effect crop | Exact effect mask and zero overlap |
| Body looks cut | One body half was frozen | Full-body key poses and motion chain |
| Hand/paw/wing looks liquid | Mesh distortion | Clean alternate key poses |
| Face/limb seam | Mask crosses anatomy | Full-scene pose from same lineage |
| Green/purple edge | Polluted translucent RGB | Reconstruct only polluted edge RGB |
| APNG ghosting/missing base | Wrong blend/disposal | Full-frame audit; use blend 0 and usually disposal 0 |
| Double character during transition | Full-subject cross-dissolve | Remove the blended transition and hold clean semantic key poses |
| Hand grips empty air | Object removed without pose reset | Regenerate complete relaxed empty hands |
| Bag is gone but strap remains | Removal list omitted components | Remove body, handle, shoulder strap and back strap explicitly |
| Character remains seated | Photo pose copied after chair removal | Regenerate a self-supporting neutral base |
| Head revision shrinks whole subject | Body scale was not locked | Specify head-only percentage and fixed sole baseline |
| Human base is not cute/readable | Ratio left implicit | Enforce `2.6–2.7` heads and inspect at 300 px |
| Prompt says 2.65 but measured base is 3+ heads | No landmark measurement gate | Record top/chin/sole coordinates and reject with the proportion validator |
| Dark oval appears under every state | Generated floor/contact shadow or CSS drop-shadow/pseudo-element | Remove it from pixels and runtime CSS; recheck all 13 states on white/dark backgrounds |

Always inspect the 12-frame storyboard, onion-skin composite, enlarged face/hands and actual-size playback. Automated bounds checks do not replace visual review.
