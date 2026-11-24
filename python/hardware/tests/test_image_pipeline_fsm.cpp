#include "image_pipeline_fsm.hpp"

#include <cassert>
#include <iostream>

using image_pipeline::Controller;
using image_pipeline::Inputs;
using image_pipeline::Phase;

int main() {
    Controller controller;

    // Starts idle.
    assert(controller.phase() == Phase::IDLE);
    assert(!controller.outputs().busy);
    assert(!controller.outputs().done);

    // Start processing.
    controller.tick(Inputs{.start = true});
    assert(controller.phase() == Phase::KEY_LOAD);
    assert(controller.outputs().key_load_enable);

    // Key must be valid before warm-up.
    controller.tick(Inputs{});
    assert(controller.phase() == Phase::KEY_LOAD);

    controller.tick(Inputs{.key_valid = true});
    assert(controller.phase() == Phase::WARMUP);
    assert(controller.outputs().warmup_enable);

    // Wait for warm-up completion.
    controller.tick(Inputs{});
    assert(controller.phase() == Phase::WARMUP);

    controller.tick(Inputs{.warmup_done = true});
    assert(controller.phase() == Phase::PERMUTATION);
    assert(controller.outputs().permutation_enable);

    // Wait for permutation completion.
    controller.tick(Inputs{});
    assert(controller.phase() == Phase::PERMUTATION);

    controller.tick(Inputs{.permutation_done = true});
    assert(controller.phase() == Phase::DIFFUSION);
    assert(controller.outputs().diffusion_enable);

    // Wait for diffusion completion.
    controller.tick(Inputs{});
    assert(controller.phase() == Phase::DIFFUSION);

    controller.tick(Inputs{.diffusion_done = true});
    assert(controller.phase() == Phase::DONE);
    assert(controller.outputs().done);
    assert(!controller.outputs().busy);

    // DONE returns to IDLE.
    controller.tick(Inputs{});
    assert(controller.phase() == Phase::IDLE);

    // Reset returns the controller to IDLE from an active phase.
    controller.tick(Inputs{.start = true});
    controller.tick(Inputs{.reset = true});
    assert(controller.phase() == Phase::IDLE);

    std::cout << "PASS: all image-pipeline FSM transitions\n";
    return 0;
}