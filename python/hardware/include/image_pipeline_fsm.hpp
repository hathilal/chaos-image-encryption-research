#ifndef IMAGE_PIPELINE_FSM_HPP
#define IMAGE_PIPELINE_FSM_HPP

namespace image_pipeline {

enum class Phase {
    IDLE,
    KEY_LOAD,
    WARMUP,
    PERMUTATION,
    DIFFUSION,
    DONE
};

struct Inputs {
    bool start = false;
    bool key_valid = false;
    bool warmup_done = false;
    bool permutation_done = false;
    bool diffusion_done = false;
    bool reset = false;
};

struct Outputs {
    Phase phase;
    bool busy;
    bool done;
    bool key_load_enable;
    bool warmup_enable;
    bool permutation_enable;
    bool diffusion_enable;
};

class Controller {
public:
    Controller() : phase_(Phase::IDLE) {}

    void tick(const Inputs& in) {
        if (in.reset) {
            phase_ = Phase::IDLE;
            return;
        }

        switch (phase_) {
        case Phase::IDLE:
            if (in.start) {
                phase_ = Phase::KEY_LOAD;
            }
            break;

        case Phase::KEY_LOAD:
            if (in.key_valid) {
                phase_ = Phase::WARMUP;
            }
            break;

        case Phase::WARMUP:
            if (in.warmup_done) {
                phase_ = Phase::PERMUTATION;
            }
            break;

        case Phase::PERMUTATION:
            if (in.permutation_done) {
                phase_ = Phase::DIFFUSION;
            }
            break;

        case Phase::DIFFUSION:
            if (in.diffusion_done) {
                phase_ = Phase::DONE;
            }
            break;

        case Phase::DONE:
            phase_ = Phase::IDLE;
            break;
        }
    }

    Outputs outputs() const {
        return {
            phase_,
            phase_ != Phase::IDLE && phase_ != Phase::DONE,
            phase_ == Phase::DONE,
            phase_ == Phase::KEY_LOAD,
            phase_ == Phase::WARMUP,
            phase_ == Phase::PERMUTATION,
            phase_ == Phase::DIFFUSION
        };
    }

    Phase phase() const {
        return phase_;
    }

private:
    Phase phase_;
};

}  // namespace image_pipeline

#endif